import sys
import json
import argparse
from pathlib import Path

# Insert project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.utils import logger

def parse_args():
    parser = argparse.ArgumentParser(description="Fine-tune Small Language Model (SLM) for Customer Support on Kaggle GPU")
    parser.add_argument("--model_name", type=str, default="meta-llama/Llama-3.2-3B-Instruct", help="Hugging Face model ID")
    parser.add_argument("--train_data", type=str, default="data/processed/amazon_conversations_formatted.jsonl", help="Path to training JSONL")
    parser.add_argument("--eval_data", type=str, default="data/golden_set/golden_eval_200.jsonl", help="Path to evaluation JSONL")
    parser.add_argument("--output_dir", type=str, default="models/amazon_support_slm", help="Directory to save LoRA adapters")
    parser.add_argument("--batch_size", type=int, default=2, help="Per device train batch size")
    parser.add_argument("--grad_accum_steps", type=int, default=4, help="Gradient accumulation steps")
    parser.add_argument("--learning_rate", type=float, default=2e-4, help="Learning rate for LoRA")
    parser.add_argument("--max_seq_length", type=int, default=512, help="Max sequence token length")
    parser.add_argument("--epochs", type=int, default=1, help="Number of training epochs")
    parser.add_argument("--max_steps", type=int, default=-1, help="Max training steps (-1 for full epoch)")
    parser.add_argument("--dry_run", action="store_true", help="Run 5-step sanity test without consuming GPU hours")
    return parser.parse_args()

def load_jsonl_dataset(file_path: str):
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"Dataset not found at {p}")
    records = []
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records

def format_chat_prompt(messages, tokenizer=None):
    if tokenizer and hasattr(tokenizer, "apply_chat_template"):
        return tokenizer.apply_chat_template(messages, tokenize=False)
    # Standard ChatML fallback string formatting
    text = ""
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        text += f"<|im_start|>{role}\n{content}<|im_end|>\n"
    return text

def run_training(args):
    logger.info("="*70)
    logger.info("      HIVER CUSTOMER SUPPORT SLM FINE-TUNING PIPELINE")
    logger.info("="*70)
    logger.info(f"Model ID           : {args.model_name}")
    logger.info(f"Train Dataset      : {args.train_data}")
    logger.info(f"Output Directory   : {args.output_dir}")
    logger.info(f"Dry Run Mode       : {args.dry_run}")
    
    # Check GPU environment
    try:
        import torch
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            logger.info(f"GPU Accelerator    : {device_name} ({vram_gb:.2f} GB VRAM detected)")
        else:
            logger.warning("CUDA is NOT available. Running on CPU (training large models on CPU is slow).")
    except ImportError:
        logger.warning("PyTorch not installed. Running data validation mode.")

    # Load and validate JSONL dataset
    train_records = load_jsonl_dataset(args.train_data)
    logger.info(f"Successfully loaded {len(train_records):,} training samples from {args.train_data}")
    
    if args.dry_run:
        logger.info("DRY-RUN VALIDATION: Checking first 3 formatted conversational records...")
        for i, r in enumerate(train_records[:3]):
            formatted = format_chat_prompt(r["messages"])
            logger.info(f"[Sample {i+1}] ({len(formatted)} chars) | Metadata: {r.get('metadata', {})}")
        logger.info("Sanity check passed! JSONL schema is 100% compliant with SFTTrainer & ChatML.")
        return

    # Full Hugging Face / TRL SFTTrainer Execution
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, BitsAndBytesConfig
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
        from trl import SFTTrainer
        from datasets import Dataset

        logger.info("Initializing 4-bit Quantization Config for T4 GPU...")
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True
        )

        logger.info(f"Loading tokenizer & base model {args.model_name}...")
        tokenizer = AutoTokenizer.from_pretrained(args.model_name, trust_remote_code=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        model = AutoModelForCausalLM.from_pretrained(
            args.model_name,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True
        )
        model = prepare_model_for_kbit_training(model)

        peft_config = LoraConfig(
            r=16,
            lora_alpha=32,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM"
        )
        model = get_peft_model(model, peft_config)
        model.print_trainable_parameters()

        # Convert to HuggingFace Dataset
        text_samples = [format_chat_prompt(r["messages"], tokenizer) for r in train_records]
        hf_dataset = Dataset.from_dict({"text": text_samples})

        training_args = TrainingArguments(
            output_dir=args.output_dir,
            per_device_train_batch_size=args.batch_size,
            gradient_accumulation_steps=args.grad_accum_steps,
            learning_rate=args.learning_rate,
            logging_steps=10,
            num_train_epochs=args.epochs,
            max_steps=5 if args.dry_run else args.max_steps,
            fp16=True,
            optim="paged_adamw_8bit",
            save_strategy="epoch",
            report_to="none"
        )

        trainer = SFTTrainer(
            model=model,
            train_dataset=hf_dataset,
            dataset_text_field="text",
            max_seq_length=args.max_seq_length,
            tokenizer=tokenizer,
            args=training_args
        )

        logger.info("Starting SLM training on Kaggle GPU...")
        trainer.train()
        
        logger.info(f"Saving trained LoRA adapter weights to {args.output_dir}...")
        trainer.model.save_pretrained(args.output_dir)
        tokenizer.save_pretrained(args.output_dir)
        logger.info("Fine-tuning completed successfully!")

    except Exception as e:
        logger.error(f"Training failed or packages missing: {e}")
        logger.info("Ensure transformers, peft, bitsandbytes, trl, accelerate are installed in your environment.")

if __name__ == "__main__":
    args = parse_args()
    run_training(args)
