from enum import Enum


class Category(str, Enum):
    """Main attack/test categories."""

    BENIGN = "BENIGN"
    ILLEGAL_ACTIVITY = "ILLEGAL_ACTIVITY"
    ETHICS = "ETHICS"
    FAIRNESS = "FAIRNESS"
    SYSTEM_PROMPT_LEAKAGE = "SYSTEM_PROMPT_LEAKAGE"
    SENSITIVE_INFORMATION_DISCLOSURE = "SENSITIVE_INFORMATION_DISCLOSURE"
    EXCESSIVE_AGENCY = "EXCESSIVE_AGENCY"
    INDIRECT_PROMPT_INJECTION = "INDIRECT_PROMPT_INJECTION"
    PRIVACY_VIOLATIONS = "PRIVACY_VIOLATIONS"
    DATA_AND_MODEL_EXTRACTION = "DATA_AND_MODEL_EXTRACTION"
    BIAS = "BIAS"
    TOXICITY = "TOXICITY"
    COMPETITION = "COMPETITION"
    ROBUSTNESS = "ROBUSTNESS"
    INDIRECT_INSTRUCTION = "INDIRECT_INSTRUCTION"


class Subcategory(str, Enum):
    """Subcategories for detailed classification."""

    # Benign subcategories
    BANKING = "BANKING"

    # Illegal Activity subcategories
    WEAPONS = "WEAPONS"
    CHILD_EXPLOITATION = "CHILD_EXPLOITATION"
    ILLEGAL_DRUGS = "ILLEGAL_DRUGS"
    VIOLENT_CRIMES = "VIOLENT_CRIMES"
    NONVIOLENT_CRIMES = "NONVIOLENT_CRIMES"
    SEX_CRIME = "SEX_CRIME"
    CYBER_CRIME = "CYBER_CRIME"

    # Ethics subcategories
    HARM_PREVENTION = "HARM_PREVENTION"
    MORAL_INTEGRITY = "MORAL_INTEGRITY"

    # Fairness subcategories
    DISCRIMINATION = "DISCRIMINATION"
    DISTRIBUTIVE_FAIRNESS = "DISTRIBUTIVE_FAIRNESS"
    PROCEDURAL_FAIRNESS = "PROCEDURAL_FAIRNESS"

    # Robustness subcategories
    HIJACKING = "HIJACKING"

    # Indirect Instruction subcategories
    RAG_INJECTION = "RAG_INJECTION"
    DOCUMENT_EMBEDDED_INSTRUCTIONS = "DOCUMENT_EMBEDDED_INSTRUCTIONS"


# Mapping from subcategory to parent category
SUBCATEGORY_TO_CATEGORY: dict[Subcategory, Category] = {
    # Benign
    Subcategory.BANKING: Category.BENIGN,
    # Illegal Activity
    Subcategory.WEAPONS: Category.ILLEGAL_ACTIVITY,
    Subcategory.CHILD_EXPLOITATION: Category.ILLEGAL_ACTIVITY,
    Subcategory.ILLEGAL_DRUGS: Category.ILLEGAL_ACTIVITY,
    Subcategory.VIOLENT_CRIMES: Category.ILLEGAL_ACTIVITY,
    Subcategory.NONVIOLENT_CRIMES: Category.ILLEGAL_ACTIVITY,
    Subcategory.SEX_CRIME: Category.ILLEGAL_ACTIVITY,
    Subcategory.CYBER_CRIME: Category.ILLEGAL_ACTIVITY,
    # Ethics
    Subcategory.HARM_PREVENTION: Category.ETHICS,
    Subcategory.MORAL_INTEGRITY: Category.ETHICS,
    # Fairness
    Subcategory.DISCRIMINATION: Category.FAIRNESS,
    Subcategory.DISTRIBUTIVE_FAIRNESS: Category.FAIRNESS,
    Subcategory.PROCEDURAL_FAIRNESS: Category.FAIRNESS,
    # Robustness
    Subcategory.HIJACKING: Category.ROBUSTNESS,
    # Indirect Instruction
    Subcategory.RAG_INJECTION: Category.INDIRECT_INSTRUCTION,
    Subcategory.DOCUMENT_EMBEDDED_INSTRUCTIONS: Category.INDIRECT_INSTRUCTION,
}


class Chatbot(str, Enum):
    """Supported LLM models / Chatbots."""

    V_GPT_41 = "GPT_41"
    V_GPT_5 = "GPT_5"


class TestCaseName(str, Enum):
    """Supported test case identifiers."""

    ILLEGAL_ACTIVITY = "illegal_activity"


class Severity(str, Enum):
    """Define whether a test case (.e. a prompt / attack) is harmful."""

    UNSAFE = "unsafe"
    SAFE = "safe"
