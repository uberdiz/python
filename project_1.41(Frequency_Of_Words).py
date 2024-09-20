#user = input("Enter a sentence with punctuation: ")
user = "Hello, hello! How are you? Are you feeling okay?"
user = user.lower()
user = user.replace(",", "")
user = user.replace("?", "")
user = user.replace(".", "")
user = user.replace("!", "")
# Split the sentence into words
user = user.split()
print(user)
overword = {}
# Count the number of words in list
for word in user:
    if word not in overword:
        overword[word] = 1
    elif word in overword:  # Increment the count if the word already exists in the dictionary. 
        overword.update({word: overword[word] + 1})
print(overword)
