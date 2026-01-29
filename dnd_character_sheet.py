#!/usr/bin/env python3
"""
D&D 5E Character Sheet PDF Filler

Takes character data as JSON and fills out the official D&D 5E fillable character sheet PDF.

Usage:
    python dnd_character_sheet.py character.json template.pdf output.pdf
    python dnd_character_sheet.py --example  # Print example JSON structure
    python dnd_character_sheet.py --list-fields template.pdf  # List all PDF form fields
"""

import argparse
import json
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject


# =============================================================================
# Data Model (Dataclasses)
# =============================================================================


@dataclass
class AbilityScores:
    """The six core ability scores."""
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10


@dataclass
class SavingThrows:
    """Saving throw proficiencies (True = proficient)."""
    strength: bool = False
    dexterity: bool = False
    constitution: bool = False
    intelligence: bool = False
    wisdom: bool = False
    charisma: bool = False


@dataclass
class Skills:
    """Skill proficiencies (True = proficient)."""
    acrobatics: bool = False
    animal_handling: bool = False
    arcana: bool = False
    athletics: bool = False
    deception: bool = False
    history: bool = False
    insight: bool = False
    intimidation: bool = False
    investigation: bool = False
    medicine: bool = False
    nature: bool = False
    perception: bool = False
    performance: bool = False
    persuasion: bool = False
    religion: bool = False
    sleight_of_hand: bool = False
    stealth: bool = False
    survival: bool = False


@dataclass
class Attack:
    """A single attack or spell."""
    name: str = ""
    attack_bonus: str = ""
    damage_type: str = ""


@dataclass
class Currency:
    """Character's money."""
    cp: int = 0  # Copper
    sp: int = 0  # Silver
    ep: int = 0  # Electrum
    gp: int = 0  # Gold
    pp: int = 0  # Platinum


@dataclass
class DeathSaves:
    """Death save successes and failures (0-3 each)."""
    successes: int = 0
    failures: int = 0


@dataclass
class SpellSlots:
    """Spell slots for a given level."""
    total: int = 0
    expended: int = 0


@dataclass
class Spellcasting:
    """Page 3 spellcasting information."""
    spellcasting_class: str = ""
    spellcasting_ability: str = ""
    spell_save_dc: str = ""
    spell_attack_bonus: str = ""
    cantrips: list[str] = field(default_factory=list)
    # Spell slots and spells by level (1-9)
    level_1_slots: SpellSlots = field(default_factory=SpellSlots)
    level_1_spells: list[str] = field(default_factory=list)
    level_2_slots: SpellSlots = field(default_factory=SpellSlots)
    level_2_spells: list[str] = field(default_factory=list)
    level_3_slots: SpellSlots = field(default_factory=SpellSlots)
    level_3_spells: list[str] = field(default_factory=list)
    level_4_slots: SpellSlots = field(default_factory=SpellSlots)
    level_4_spells: list[str] = field(default_factory=list)
    level_5_slots: SpellSlots = field(default_factory=SpellSlots)
    level_5_spells: list[str] = field(default_factory=list)
    level_6_slots: SpellSlots = field(default_factory=SpellSlots)
    level_6_spells: list[str] = field(default_factory=list)
    level_7_slots: SpellSlots = field(default_factory=SpellSlots)
    level_7_spells: list[str] = field(default_factory=list)
    level_8_slots: SpellSlots = field(default_factory=SpellSlots)
    level_8_spells: list[str] = field(default_factory=list)
    level_9_slots: SpellSlots = field(default_factory=SpellSlots)
    level_9_spells: list[str] = field(default_factory=list)


@dataclass
class Appearance:
    """Page 2 appearance information."""
    age: str = ""
    height: str = ""
    weight: str = ""
    eyes: str = ""
    skin: str = ""
    hair: str = ""


@dataclass
class Character:
    """Complete D&D 5E character data."""
    # Page 1 - Header
    character_name: str = ""
    class_level: str = ""
    background: str = ""
    player_name: str = ""
    race: str = ""
    alignment: str = ""
    experience_points: str = ""

    # Page 1 - Core Stats
    ability_scores: AbilityScores = field(default_factory=AbilityScores)
    inspiration: bool = False
    proficiency_bonus: str = ""

    # Page 1 - Saving Throws & Skills
    saving_throws: SavingThrows = field(default_factory=SavingThrows)
    skills: Skills = field(default_factory=Skills)
    passive_perception: str = ""

    # Page 1 - Combat
    armor_class: str = ""
    initiative: str = ""
    speed: str = ""
    hit_point_maximum: str = ""
    current_hit_points: str = ""
    temporary_hit_points: str = ""
    hit_dice_total: str = ""
    hit_dice: str = ""
    death_saves: DeathSaves = field(default_factory=DeathSaves)

    # Page 1 - Attacks
    attacks: list[Attack] = field(default_factory=list)
    attacks_notes: str = ""

    # Page 1 - Equipment & Currency
    currency: Currency = field(default_factory=Currency)
    equipment: str = ""

    # Page 1 - Personality
    personality_traits: str = ""
    ideals: str = ""
    bonds: str = ""
    flaws: str = ""

    # Page 1 - Other
    other_proficiencies_languages: str = ""
    features_traits: str = ""

    # Page 2 - Appearance & Background
    appearance: Appearance = field(default_factory=Appearance)
    character_appearance: str = ""
    character_backstory: str = ""
    allies_organizations: str = ""
    allies_organizations_name: str = ""
    additional_features_traits: str = ""
    treasure: str = ""

    # Page 3 - Spellcasting
    spellcasting: Spellcasting = field(default_factory=Spellcasting)


# =============================================================================
# PDF Field Mapping
# =============================================================================

def calculate_modifier(score: int) -> int:
    """Calculate ability modifier from score (as integer)."""
    return (score - 10) // 2


def format_modifier(mod: int) -> str:
    """Format a modifier as a string with +/- sign."""
    return f"+{mod}" if mod >= 0 else str(mod)


def parse_proficiency_bonus(bonus_str: str) -> int:
    """Parse proficiency bonus from string like '+3' to integer."""
    if not bonus_str:
        return 0
    return int(bonus_str.replace("+", ""))


# Skill to ability mapping (D&D 5E rules)
SKILL_ABILITIES = {
    "acrobatics": "dexterity",
    "animal_handling": "wisdom",
    "arcana": "intelligence",
    "athletics": "strength",
    "deception": "charisma",
    "history": "intelligence",
    "insight": "wisdom",
    "intimidation": "charisma",
    "investigation": "intelligence",
    "medicine": "wisdom",
    "nature": "intelligence",
    "perception": "wisdom",
    "performance": "charisma",
    "persuasion": "charisma",
    "religion": "intelligence",
    "sleight_of_hand": "dexterity",
    "stealth": "dexterity",
    "survival": "wisdom",
}


def get_field_mapping(char: Character) -> dict[str, str]:
    """
    Map character data to PDF form field names.

    Note: Field names come from the official WotC 5E character sheet.
    Use --list-fields to see all available fields in your PDF.
    """
    fields = {}

    # Page 1 - Header
    fields["CharacterName"] = char.character_name
    fields["ClassLevel"] = char.class_level
    fields["Background"] = char.background
    fields["PlayerName"] = char.player_name
    fields["Race "] = char.race  # Note: has trailing space in PDF
    fields["Alignment"] = char.alignment
    fields["XP"] = char.experience_points

    # Ability Scores and Modifiers
    # Note: PDF uses different modifier field naming
    str_mod = calculate_modifier(char.ability_scores.strength)
    dex_mod = calculate_modifier(char.ability_scores.dexterity)
    con_mod = calculate_modifier(char.ability_scores.constitution)
    int_mod = calculate_modifier(char.ability_scores.intelligence)
    wis_mod = calculate_modifier(char.ability_scores.wisdom)
    cha_mod = calculate_modifier(char.ability_scores.charisma)

    fields["STR"] = str(char.ability_scores.strength)
    fields["STRmod"] = format_modifier(str_mod)
    fields["DEX"] = str(char.ability_scores.dexterity)
    fields["DEXmod "] = format_modifier(dex_mod)  # trailing space
    fields["CON"] = str(char.ability_scores.constitution)
    fields["CONmod"] = format_modifier(con_mod)
    fields["INT"] = str(char.ability_scores.intelligence)
    fields["INTmod"] = format_modifier(int_mod)
    fields["WIS"] = str(char.ability_scores.wisdom)
    fields["WISmod"] = format_modifier(wis_mod)
    fields["CHA"] = str(char.ability_scores.charisma)
    fields["CHamod"] = format_modifier(cha_mod)  # Note: lowercase 'a'

    # Build ability modifier lookup for skill calculations
    ability_mods = {
        "strength": str_mod,
        "dexterity": dex_mod,
        "constitution": con_mod,
        "intelligence": int_mod,
        "wisdom": wis_mod,
        "charisma": cha_mod,
    }
    prof_bonus = parse_proficiency_bonus(char.proficiency_bonus)

    # Proficiency Bonus
    fields["ProfBonus"] = char.proficiency_bonus

    # Inspiration (checkbox)
    if char.inspiration:
        fields["Inspiration"] = "Yes"

    # Saving Throws - calculate modifier for each
    # Formula: ability_modifier + (proficiency_bonus if proficient else 0)
    st_field_map = {
        # (field_name, ability_name, is_proficient)
        "ST Strength": ("strength", char.saving_throws.strength),
        "ST Dexterity": ("dexterity", char.saving_throws.dexterity),
        "ST Constitution": ("constitution", char.saving_throws.constitution),
        "ST Intelligence": ("intelligence", char.saving_throws.intelligence),
        "ST Wisdom": ("wisdom", char.saving_throws.wisdom),
        "ST Charisma": ("charisma", char.saving_throws.charisma),
    }
    for field_name, (ability, is_proficient) in st_field_map.items():
        ability_mod = ability_mods[ability]
        save_mod = ability_mod + (prof_bonus if is_proficient else 0)
        fields[field_name] = format_modifier(save_mod)

    # Saving throw proficiency checkboxes
    st_checkbox_map = {
        "Check Box 11": char.saving_throws.strength,
        "Check Box 18": char.saving_throws.dexterity,
        "Check Box 19": char.saving_throws.constitution,
        "Check Box 20": char.saving_throws.intelligence,
        "Check Box 21": char.saving_throws.wisdom,
        "Check Box 22": char.saving_throws.charisma,
    }
    for field_name, is_proficient in st_checkbox_map.items():
        if is_proficient:
            fields[field_name] = NameObject("/Yes")

    # Skills - calculate modifier for each skill
    # Formula: ability_modifier + (proficiency_bonus if proficient else 0)
    # Field names are for the text fields showing the modifier value
    skill_field_map = {
        # (field_name, skill_attr_name)
        "Acrobatics": "acrobatics",
        "Animal": "animal_handling",
        "Arcana": "arcana",
        "Athletics": "athletics",
        "Deception ": "deception",  # trailing space
        "History ": "history",  # trailing space
        "Insight": "insight",
        "Intimidation": "intimidation",
        "Investigation ": "investigation",  # trailing space
        "Medicine": "medicine",
        "Nature": "nature",
        "Perception ": "perception",  # trailing space
        "Performance": "performance",
        "Persuasion": "persuasion",
        "Religion": "religion",
        "SleightofHand": "sleight_of_hand",
        "Stealth ": "stealth",  # trailing space
        "Survival": "survival",
    }

    for field_name, skill_attr in skill_field_map.items():
        is_proficient = getattr(char.skills, skill_attr)
        governing_ability = SKILL_ABILITIES[skill_attr]
        ability_mod = ability_mods[governing_ability]
        skill_mod = ability_mod + (prof_bonus if is_proficient else 0)
        fields[field_name] = format_modifier(skill_mod)

    # Skill proficiency checkboxes
    # The PDF uses "Check Box NN" for these - mapping based on typical sheet order
    skill_checkbox_map = {
        "Check Box 23": char.skills.acrobatics,
        "Check Box 24": char.skills.animal_handling,
        "Check Box 25": char.skills.arcana,
        "Check Box 26": char.skills.athletics,
        "Check Box 27": char.skills.deception,
        "Check Box 28": char.skills.history,
        "Check Box 29": char.skills.insight,
        "Check Box 30": char.skills.intimidation,
        "Check Box 31": char.skills.investigation,
        "Check Box 32": char.skills.medicine,
        "Check Box 33": char.skills.nature,
        "Check Box 34": char.skills.perception,
        "Check Box 35": char.skills.performance,
        "Check Box 36": char.skills.persuasion,
        "Check Box 37": char.skills.religion,
        "Check Box 38": char.skills.sleight_of_hand,
        "Check Box 39": char.skills.stealth,
        "Check Box 40": char.skills.survival,
    }
    for field_name, is_proficient in skill_checkbox_map.items():
        if is_proficient:
            fields[field_name] = NameObject("/Yes")

    # Passive Perception
    fields["Passive"] = char.passive_perception

    # Combat Stats
    fields["AC"] = char.armor_class
    fields["Initiative"] = char.initiative
    fields["Speed"] = char.speed
    fields["HPMax"] = char.hit_point_maximum
    fields["HPCurrent"] = char.current_hit_points
    fields["HPTemp"] = char.temporary_hit_points
    fields["HDTotal"] = char.hit_dice_total
    fields["HD"] = char.hit_dice

    # Death Saves - uses Check Box fields (11-13 success, 14-16 failure based on PDF)
    # These checkbox field names vary - would need more investigation to map correctly

    # Attacks (up to 3)
    if len(char.attacks) > 0:
        fields["Wpn Name"] = char.attacks[0].name
        fields["Wpn1 AtkBonus"] = char.attacks[0].attack_bonus
        fields["Wpn1 Damage"] = char.attacks[0].damage_type
    if len(char.attacks) > 1:
        fields["Wpn Name 2"] = char.attacks[1].name
        fields["Wpn2 AtkBonus "] = char.attacks[1].attack_bonus  # trailing space
        fields["Wpn2 Damage "] = char.attacks[1].damage_type  # trailing space
    if len(char.attacks) > 2:
        fields["Wpn Name 3"] = char.attacks[2].name
        fields["Wpn3 AtkBonus  "] = char.attacks[2].attack_bonus  # two trailing spaces
        fields["Wpn3 Damage "] = char.attacks[2].damage_type  # trailing space

    # Attacks notes
    fields["AttacksSpellcasting"] = char.attacks_notes

    # Currency
    fields["CP"] = str(char.currency.cp) if char.currency.cp else ""
    fields["SP"] = str(char.currency.sp) if char.currency.sp else ""
    fields["EP"] = str(char.currency.ep) if char.currency.ep else ""
    fields["GP"] = str(char.currency.gp) if char.currency.gp else ""
    fields["PP"] = str(char.currency.pp) if char.currency.pp else ""

    # Equipment
    fields["Equipment"] = char.equipment

    # Personality
    fields["PersonalityTraits "] = char.personality_traits  # trailing space
    fields["Ideals"] = char.ideals
    fields["Bonds"] = char.bonds
    fields["Flaws"] = char.flaws

    # Other proficiencies & languages
    fields["ProficienciesLang"] = char.other_proficiencies_languages

    # Features & Traits
    fields["Features and Traits"] = char.features_traits

    # Page 2 - Appearance
    fields["CharacterName 2"] = char.character_name
    fields["Age"] = char.appearance.age
    fields["Height"] = char.appearance.height
    fields["Weight"] = char.appearance.weight
    fields["Eyes"] = char.appearance.eyes
    fields["Skin"] = char.appearance.skin
    fields["Hair"] = char.appearance.hair

    # Page 2 - Text areas (field name is "Allies" not "AlliesOrganizations")
    fields["Backstory"] = char.character_backstory
    fields["Allies"] = char.allies_organizations
    fields["FactionName"] = char.allies_organizations_name
    fields["Feat+Traits"] = char.additional_features_traits
    fields["Treasure"] = char.treasure

    # Page 3 - Spellcasting
    fields["Spellcasting Class 2"] = char.spellcasting.spellcasting_class
    fields["SpellcastingAbility 2"] = char.spellcasting.spellcasting_ability
    fields["SpellSaveDC  2"] = char.spellcasting.spell_save_dc  # two spaces before 2
    fields["SpellAtkBonus 2"] = char.spellcasting.spell_attack_bonus

    # Cantrips - field names are Spells 1014-1021 for cantrips (8 slots)
    cantrip_fields = ["Spells 1014", "Spells 1015", "Spells 1016", "Spells 1017",
                      "Spells 1018", "Spells 1019", "Spells 1020", "Spells 1021"]
    for i, cantrip in enumerate(char.spellcasting.cantrips[:8]):
        fields[cantrip_fields[i]] = cantrip

    # Spell slots - PDF uses SlotsTotal 19-27 for levels 1-9
    # and SlotsRemaining 19-27 for expended slots
    slot_field_offset = 18  # level 1 = field 19, level 9 = field 27
    for level in range(1, 10):
        field_num = level + slot_field_offset
        slots = getattr(char.spellcasting, f"level_{level}_slots")
        if slots.total:
            fields[f"SlotsTotal {field_num}"] = str(slots.total)
        if slots.expended:
            fields[f"SlotsRemaining {field_num}"] = str(slots.expended)

    # Spell lists by level - field naming is complex, would need investigation
    # The fields are Spells 1022-1034 for level 1, etc.
    # For now, just map level 1 spells as an example
    level_1_spell_fields = [f"Spells {i}" for i in range(1022, 1035)]
    for i, spell in enumerate(char.spellcasting.level_1_spells[:13]):
        fields[level_1_spell_fields[i]] = spell

    return fields


# =============================================================================
# PDF Operations
# =============================================================================

def list_pdf_fields(pdf_path: Path) -> list[str]:
    """List all form field names in the PDF."""
    reader = PdfReader(pdf_path)
    fields = []
    if reader.get_form_text_fields():
        fields.extend(reader.get_form_text_fields().keys())
    if "/AcroForm" in reader.trailer["/Root"]:
        acro_form = reader.trailer["/Root"]["/AcroForm"]
        if "/Fields" in acro_form:
            for field_ref in acro_form["/Fields"]:
                field_obj = field_ref.get_object()
                if "/T" in field_obj:
                    field_name = field_obj["/T"]
                    if field_name not in fields:
                        fields.append(field_name)
    return sorted(fields)


def fill_pdf(template_path: Path, output_path: Path, char: Character) -> None:
    """Fill the PDF template with character data."""
    reader = PdfReader(template_path)
    writer = PdfWriter()

    # Clone the template
    writer.append(reader)

    # Get field mapping
    field_data = get_field_mapping(char)

    # Fill in the fields
    writer.update_page_form_field_values(writer.pages[0], field_data)
    if len(writer.pages) > 1:
        writer.update_page_form_field_values(writer.pages[1], field_data)
    if len(writer.pages) > 2:
        writer.update_page_form_field_values(writer.pages[2], field_data)

    # Write output
    with open(output_path, "wb") as f:
        writer.write(f)

    print(f"Character sheet saved to: {output_path}")


def character_from_dict(data: dict) -> Character:
    """Create a Character from a dictionary (parsed JSON)."""
    # Handle nested dataclasses
    if "ability_scores" in data and isinstance(data["ability_scores"], dict):
        data["ability_scores"] = AbilityScores(**data["ability_scores"])

    if "saving_throws" in data and isinstance(data["saving_throws"], dict):
        data["saving_throws"] = SavingThrows(**data["saving_throws"])

    if "skills" in data and isinstance(data["skills"], dict):
        data["skills"] = Skills(**data["skills"])

    if "death_saves" in data and isinstance(data["death_saves"], dict):
        data["death_saves"] = DeathSaves(**data["death_saves"])

    if "currency" in data and isinstance(data["currency"], dict):
        data["currency"] = Currency(**data["currency"])

    if "appearance" in data and isinstance(data["appearance"], dict):
        data["appearance"] = Appearance(**data["appearance"])

    if "attacks" in data and isinstance(data["attacks"], list):
        data["attacks"] = [Attack(**a) if isinstance(a, dict) else a for a in data["attacks"]]

    if "spellcasting" in data and isinstance(data["spellcasting"], dict):
        sc = data["spellcasting"]
        # Handle nested SpellSlots
        for level in range(1, 10):
            key = f"level_{level}_slots"
            if key in sc and isinstance(sc[key], dict):
                sc[key] = SpellSlots(**sc[key])
        data["spellcasting"] = Spellcasting(**sc)

    return Character(**data)


def get_example_character() -> Character:
    """Return an example character for demonstration."""
    return Character(
        character_name="Thorn Ironbark",
        class_level="Fighter 5",
        background="Soldier",
        player_name="Example Player",
        race="Half-Orc",
        alignment="Lawful Good",
        experience_points="6500",
        ability_scores=AbilityScores(
            strength=18,
            dexterity=14,
            constitution=16,
            intelligence=10,
            wisdom=12,
            charisma=8,
        ),
        inspiration=False,
        proficiency_bonus="+3",
        saving_throws=SavingThrows(strength=True, constitution=True),
        skills=Skills(
            athletics=True,
            intimidation=True,
            perception=True,
            survival=True,
        ),
        passive_perception="14",
        armor_class="18",
        initiative="+2",
        speed="30 ft",
        hit_point_maximum="44",
        current_hit_points="44",
        temporary_hit_points="",
        hit_dice_total="5d10",
        hit_dice="5d10",
        death_saves=DeathSaves(successes=0, failures=0),
        attacks=[
            Attack(name="Greatsword", attack_bonus="+7", damage_type="2d6+4 slashing"),
            Attack(name="Javelin", attack_bonus="+7", damage_type="1d6+4 piercing"),
            Attack(name="Handaxe", attack_bonus="+7", damage_type="1d6+4 slashing"),
        ],
        attacks_notes="Extra Attack: Can attack twice per Attack action.\nSecond Wind: Regain 1d10+5 HP as bonus action (1/short rest).",
        currency=Currency(cp=0, sp=15, ep=0, gp=75, pp=0),
        equipment="Greatsword\nChain mail\n2 Handaxes\n4 Javelins\nExplorer's pack\nInsignia of rank\nTrophy from fallen enemy\nDice set\nCommon clothes",
        personality_traits="I face problems head-on. A simple, direct solution is the best path to success.",
        ideals="Responsibility. I do what I must and obey just authority.",
        bonds="Those who fight beside me are worth dying for.",
        flaws="I made a terrible mistake in battle that cost many lives—I would do anything to keep that secret.",
        other_proficiencies_languages="Languages: Common, Orc\n\nArmor: All armor, shields\nWeapons: Simple weapons, martial weapons\nTools: Dice set, vehicles (land)",
        features_traits="Relentless Endurance\nSavage Attacks\nFighting Style: Great Weapon Fighting\nSecond Wind\nAction Surge (1 use)\nExtra Attack",
        appearance=Appearance(
            age="28",
            height="6'4\"",
            weight="250 lbs",
            eyes="Yellow",
            skin="Gray-green",
            hair="Black",
        ),
        character_appearance="Massive half-orc with prominent tusks and numerous battle scars. Wears well-maintained chain mail with a military insignia.",
        character_backstory="Thorn served in the king's army for a decade before a catastrophic battle changed everything...",
        allies_organizations="The Iron Legion (former military unit)",
        allies_organizations_name="The Iron Legion",
        additional_features_traits="",
        treasure="A lucky gold coin from my first battle",
    )


def print_example_json() -> None:
    """Print example JSON structure."""
    example = get_example_character()
    # Convert to dict, handling nested dataclasses
    def to_serializable(obj):
        if hasattr(obj, "__dataclass_fields__"):
            return {k: to_serializable(v) for k, v in asdict(obj).items()}
        elif isinstance(obj, list):
            return [to_serializable(item) for item in obj]
        return obj

    print(json.dumps(to_serializable(example), indent=2))


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Fill D&D 5E character sheet PDF from JSON data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s character.json template.pdf output.pdf
  %(prog)s --example > my_character.json
  %(prog)s --list-fields template.pdf
        """,
    )

    parser.add_argument(
        "character_json",
        nargs="?",
        help="Path to character JSON file",
    )
    parser.add_argument(
        "template_pdf",
        nargs="?",
        help="Path to fillable PDF template",
    )
    parser.add_argument(
        "output_pdf",
        nargs="?",
        help="Path for output PDF",
    )
    parser.add_argument(
        "--example",
        action="store_true",
        help="Print example JSON structure and exit",
    )
    parser.add_argument(
        "--list-fields",
        metavar="PDF",
        help="List all form fields in the PDF and exit",
    )

    args = parser.parse_args()

    if args.example:
        print_example_json()
        return

    if args.list_fields:
        fields = list_pdf_fields(Path(args.list_fields))
        print("Form fields in PDF:")
        for f in fields:
            print(f"  {f!r}")
        return

    if not all([args.character_json, args.template_pdf, args.output_pdf]):
        parser.print_help()
        sys.exit(1)

    # Load character data
    with open(args.character_json) as f:
        char_data = json.load(f)

    char = character_from_dict(char_data)

    # Fill the PDF
    fill_pdf(
        Path(args.template_pdf),
        Path(args.output_pdf),
        char,
    )


if __name__ == "__main__":
    main()
