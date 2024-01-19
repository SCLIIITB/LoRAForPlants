# LoRAForPlants
## Pre-requisits
1. clone the repo
2. cd to the clones repo
3. unzip src.zip
4. create two folders "input" and "outputs" in the current directory

## Download the dataset
https://drive.google.com/drive/folders/1pC28yk-vd_O-DxG7kG7pRgvWNGsMl6Ud?usp=sharing

## Run LoRA with Resnet-50 Backbone
python3 LoRA.py

## Run LoRA with ViT Backbone
python3 LoRA_vit.py

## Run Full Fine Tuning (Full FT)
python3 train.py --model resnet50 --epochs 100 --finetune True

## Run Selective finetuning (FT)
python3 train.py --model resnet50 --epochs 100 --finetune partial

## Test the Full FT or FT model on test dataset
python3 test.py --weights ../outputs/resnet50/best_model.pth --model resnet50 --custom_flag False

## Note
--model can take values: "resnet50" or "vit"
--finetune can take values: "True" to run the full FT experiments, "partial" to run the FT experiments in the paper.
-- weights is the path to the trained  model.
