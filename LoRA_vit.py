# -*- coding: utf-8 -*-
"""Another copy of Image_Classification_Using_LORA

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1d-NLwJspZqzQMWx7UVSD306U09aiflFg
"""

#INSTALLING DEPENDENCIES
#!pip install transformers accelerate evaluate datasets peft -q

# #Authentication jazz
# from huggingface_hub import notebook_login

# notebook_login()

import transformers
import accelerate
import peft
from torch.utils.data import Dataset
from torchvision import transforms, datasets
from pathlib import Path

print(f"Transformers version: {transformers.__version__}")
print(f"Accelerate version: {accelerate.__version__}")
print(f"PEFT version: {peft.__version__}")
"Transformers version: 4.27.4"
"Accelerate version: 0.18.0"
"PEFT version: 0.2.0"
access_token = "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"
#SELECTING A MODEL CHECKPOINT TO FINETUNE
model_checkpoint =  "google/vit-base-patch16-224-in21k"#"microsoft/resnet-50"
data_dir = './input'
train_data_dir = './input/pvd/'
test_data_dir = './input/test/'


image_size = 128
#LOADING THE DATASET
from datasets import load_dataset
def _validate_root_dir(root):
    # todo: raise exception or warning
    pass

def _validate_train_flag(train: bool, valid: bool, test: bool):
    assert [train, valid, test].count(True)==1, "one of train, valid & test must be true."

class CustomDataset(Dataset):
    def __init__(self, root,
                 train: bool = False, valid: bool = False, test: bool = False,
                 transform=None, target_transform=None,):

        _validate_root_dir(root)
        _validate_train_flag(train, valid, test)
        self.transform = transform
        self.target_transform = target_transform
        if train:
            self.data_dir = Path(root)/'pvd'
        elif valid:
            self.data_dir = Path(root)/'test'#'test'
        elif test:
            self.data_dir = Path(root)/'test'

        self._image_paths = sorted(
            list(self.data_dir.glob("**/*.JPG"))+
            list(self.data_dir.glob("**/*.jpg"))+
            list(self.data_dir.glob("**/*.jpeg"))+
            list(self.data_dir.glob("**/*.png")))
        
        # Create a mapping from label string to integer
        self.label_mapping = {label: idx for idx, label in enumerate(sorted(set(str(i.parent.name) for i in self._image_paths)))}

        self._image_labels = [self.label_mapping[str(i.parent.name)] for i in self._image_paths]
        assert len(self._image_paths) == len(self._image_labels)
    def print_label_mapping(self):
        print("Label Mapping:")
        for label, idx in self.label_mapping.items():
            print(f"{label}: {idx}")
    def get_label_names(self):
        print("Label Mapping:")
        for label, idx in self.label_mapping.items():
            print(f"{label}: {idx}")
        return self.label_mapping.keys()

    def __len__(self):
        return len(self._image_paths)

    def __getitem__(self, idx):
        try:
            print("idx:::", idx)
            x = Image.open(str(self._image_paths[idx]))
            y = self._image_labels[idx]
            if self.transform:
                x = self.transform(x)
            if self.target_transform:
                y = self.target_transform(x)
            return x, y
        except:
            print("Image not working: ", str(self._image_paths[idx]))

    def get_labels(self):
        return self._image_labels
train_ds = load_dataset("imagefolder", data_dir=train_data_dir, split='train')
# CustomDataset(
#     root=data_dir,
#     train=True,
#     transform=transforms.Compose(
#         [
#             # If images have 1 channel, our model will expect 3-channel images
#             # transforms.Grayscale(num_output_channels=3),
#             transforms.Resize([image_size,image_size]),
#             transforms.CenterCrop(image_size),
#             transforms.ToTensor(),
#             transforms.Normalize(mean=[0.485, 0.456, 0.406],
#                                  std=[0.229, 0.224, 0.225]),
#         ]
#     ),
# )#load_dataset("food101", split="train[:5000]")
val_ds =  load_dataset("imagefolder", data_dir=test_data_dir, split='train')
import os
label_name = os.listdir(train_data_dir)
#PREPARING THE DATASET
labels = label_name#train_ds.features["label"].names
label2id, id2label = dict(), dict()
for i, label in enumerate(labels):
    label2id[label] = i
    id2label[i] = label

# print(id2label[2])


#Loading Transform's image processor as Transform is the model we are fine tuning
from transformers import AutoImageProcessor, ResNetForImageClassification

#model = ResNetForImageClassification.from_pretrained("microsoft/resnet-50")
image_processor = AutoImageProcessor.from_pretrained(model_checkpoint)



from torchvision.transforms import (
    CenterCrop,
    Compose,
    Normalize,
    RandomHorizontalFlip,
    RandomResizedCrop,
    Resize,
    ToTensor,
)

normalize = Normalize(mean= [0.485, 0.456, 0.406] , std=[0.229, 0.224, 0.225])
train_transforms = Compose(
    [
        RandomResizedCrop(224),
        RandomHorizontalFlip(),
        ToTensor(),
        normalize,
    ]
)

val_transforms = Compose(
    [
        Resize(224),
        CenterCrop(224),
        ToTensor(),
        normalize,
    ]
)


def preprocess_train(example_batch):
    """Apply train_transforms across a batch."""
    example_batch["pixel_values"] = [train_transforms(image.convert("RGB")) for image in example_batch["image"]]
    return example_batch


def preprocess_val(example_batch):
    """Apply val_transforms across a batch."""
    example_batch["pixel_values"] = [val_transforms(image.convert("RGB")) for image in example_batch["image"]]
    return example_batch

#Split dataset into train and validation sets
#splits = dataset.train_test_split(test_size=0.1)
# train_ds = splits["train"]
# val_ds = splits["test"]

#Setting transformaton functions for the datasets accordingly
train_ds.set_transform(preprocess_train)
val_ds.set_transform(preprocess_val)

#LOADING AND PREPARING A MODEL
#helper function to check the total number of parameters a model has and how many are trainable
def print_trainable_parameters(model):
    trainable_params = 0
    all_param = 0
    for _, param in model.named_parameters():
        all_param += param.numel()
        if param.requires_grad:
            trainable_params += param.numel()
    print(
        f"trainable params: {trainable_params} || all params: {all_param} || trainable%: {100 * trainable_params / all_param:.2f}"
    )


"""model = AutoModelForImageClassification.from_pretrained(
    model_checkpoint,
    label2id=label2id,
    id2label=id2label,
    ignore_mismatched_sizes=True,  # provide this in case you're planning to fine-tune an already fine-tuned checkpoint
)"""
from transformers import AutoModelForImageClassification, TrainingArguments, Trainer

model = AutoModelForImageClassification.from_pretrained(
    model_checkpoint,
    label2id=label2id,
    id2label=id2label,
    ignore_mismatched_sizes=True,  # provide this in case you're planning to fine-tune an already fine-tuned checkpoint
)
#model = ResNetForImageClassification.from_pretrained(model_checkpoint, label2id=label2id, id2label=id2label, ignore_mismatched_sizes=True)

#Checking number of trainable parameters on original model
print_trainable_parameters(model)
"trainable params: 85876325 || all params: 85876325 || trainable%: 100.00"

# #Using peft model to wrap the original model so that update matrices are added to their respective places
# from peft import LoraConfig, get_peft_model

# config = LoraConfig(
#     r=16,
#     lora_alpha=16,
#     target_modules=["query", "value"],
#     lora_dropout=0.1,
#     bias="none",
#     modules_to_save=["classifier"],
# )
# lora_model = get_peft_model(model, config)
# print_trainable_parameters(lora_model)
# "trainable params: 667493 || all params: 86466149 || trainable%: 0.77"

# Print the names of all modules in the base model
print(model)
print()
print("modules:")
for name, module in model.named_modules():
    print(name)

#V2
#Using peft model to wrap the original model so that update matrices are added to their respective places
from peft import LoraConfig, get_peft_model

config = LoraConfig(
    r=16,
    lora_alpha=16,
    target_modules=["query", "value"],
    #target_modules=["resnet.encoder.stages.3.layers.2.layer.0.convolution", "resnet.encoder.stages.3.layers.2.layer.1.convolution",
    #"resnet.encoder.stages.3.layers.2.layer.2.convolution"],
    lora_dropout=0.1,
    bias="none",
    modules_to_save=["classifier"],
)
lora_model = get_peft_model(model, config)
print_trainable_parameters(lora_model)
"trainable params: 667493 || all params: 86466149 || trainable%: 0.77"

#DEFINING TRAINING ARGUMENTS
from transformers import TrainingArguments, Trainer


model_name = model_checkpoint.split("/")[-1]
batch_size = 128

args = TrainingArguments(
    f"{model_name}-finetuned-lora-food101",
    remove_unused_columns=False,
    evaluation_strategy="epoch",
    save_strategy="epoch",
    learning_rate=5e-3,
    per_device_train_batch_size=batch_size,
    gradient_accumulation_steps=4,
    per_device_eval_batch_size=batch_size,
    fp16=True,
    num_train_epochs=100,
    logging_steps=10,
    load_best_model_at_end=True,
    metric_for_best_model="accuracy",
    push_to_hub=True,
    label_names=["labels"],
)

#PREPARING EVALUATION METRIC
import numpy as np
import evaluate

metric = evaluate.load("accuracy")


def compute_metrics(eval_pred):
    """Computes accuracy on a batch of predictions"""
    predictions = np.argmax(eval_pred.predictions, axis=1)
    return metric.compute(predictions=predictions, references=eval_pred.label_ids)

#Define collation function
""" A collation function is used by Trainer to gather a batch of training and evaluation examples and prepare them in a format that is
 acceptable by the underlying model. """

import torch


def collate_fn(examples):
    pixel_values = torch.stack([example["pixel_values"] for example in examples])
    labels = torch.tensor([example["label"] for example in examples])
    return {"pixel_values": pixel_values, "labels": labels}

#TRAIN AND VALIDATE
trainer = Trainer(
    lora_model,
    args,
    train_dataset=train_ds,
    eval_dataset=val_ds,
    tokenizer=image_processor,
    compute_metrics=compute_metrics,
    data_collator=collate_fn,
)
train_results = trainer.train()
print(trainer.evaluate(val_ds))
# repo_name = f"repo Name"
# lora_model.push_to_hub(repo_name)

