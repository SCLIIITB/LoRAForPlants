# LoRAForPlants
python3 LoRA.py

## Full Fine Tuning (Full FT)
python3 train.py --model resnet50 --epochs 100 --finetune True

## Selective finetuning (FT)
python3 train.py --model resnet50 --epochs 100 --finetune partial

## Test the Full FT or FT model on test dataset
python3 test.py --weights ../outputs/resnet50/best_model.pth --model resnet50 --custom_flag False
