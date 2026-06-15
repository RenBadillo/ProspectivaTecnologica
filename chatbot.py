# Use a pipeline as a high-level helper
from transformers import pipeline
# Load model directly
from transformers import AutoTokenizer, AutoModelForCausalLM

pipe = pipeline("text-generation", model="openbmb/MiniCPM5-1B")
messages = [
    {"role": "user", "content": "Who are you?"},
]
pipe(messages)

tokenizer = AutoTokenizer.from_pretrained("openbmb/MiniCPM5-1B")
model = AutoModelForCausalLM.from_pretrained("openbmb/MiniCPM5-1B")
messages = [
    {"role": "user", "content": "Who are you?"},
]
inputs = tokenizer.apply_chat_template(
	messages,
	add_generation_prompt=True,
	tokenize=True,
	return_dict=True,
	return_tensors="pt",
).to(model.device)

outputs = model.generate(**inputs, max_new_tokens=40)
print(tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:]))