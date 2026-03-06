#  Copyright (c) 2026.
#  Florian Emanuel Sauer

ENTITIES = [
    "CREDIT_CARD",
    "CRYPTO",
    "EMAIL_ADDRESS",
    "IBAN_CODE",
    "IP_ADDRESS",
    "PHONE_NUMBER",
    "CREDIT_CARD_RE",
]

# todo: if necessary, adjust the topics here and in the docker container python script
SENSITIVE_TOPICS = [
    "being ridiculed or judged",
    "getting rejected",
    "being ignored",
    "violence in the news",
    "sexual harassment or unwanted touching",
    "physical illness or injury",
    "violence", "sensitive information", "role changes", "authority changes",
    "function changes", "system instructions", "system information", "weapons", "illegal activities",
    "employee information", "internal information", "fraud", "crime", "drugs", "drug production",
    "cybercrime"
]
