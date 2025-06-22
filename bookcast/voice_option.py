from enum import StrEnum
from pydantic import BaseModel


class Sex(StrEnum):
    male = "男性"
    female = "女性"


class VoiceOption(BaseModel):
    voice_name: str
    description: str
    sex: Sex


class VoiceOptions(BaseModel):
    options: list[VoiceOption]


voice_options = VoiceOptions(
    options=[
        VoiceOption(voice_name="Zephyr", description="明るい", sex=Sex.female),
        VoiceOption(voice_name="Puck", description="アップビート", sex=Sex.male),
        VoiceOption(voice_name="Charon", description="情報に富んでいる", sex=Sex.male),
        VoiceOption(voice_name="Kore", description="固い", sex=Sex.female),
        VoiceOption(voice_name="Fenrir", description="興奮しやすい", sex=Sex.male),
        VoiceOption(voice_name="Leda", description="若々しい", sex=Sex.female),
        VoiceOption(voice_name="Orus", description="固い", sex=Sex.male),
        VoiceOption(voice_name="Aoede", description="爽やかな", sex=Sex.female),
        VoiceOption(voice_name="Callirrhoe", description="おおらか", sex=Sex.female),
        VoiceOption(voice_name="Autonoe", description="明るい", sex=Sex.female),
        VoiceOption(voice_name="Enceladus", description="息づかい", sex=Sex.male),
        VoiceOption(voice_name="Iapetus", description="クリア", sex=Sex.male),
        VoiceOption(voice_name="Umbriel", description="気楽な", sex=Sex.male),
        VoiceOption(voice_name="Algieba", description="流暢", sex=Sex.male),
        VoiceOption(voice_name="Despina", description="流暢", sex=Sex.female),
        VoiceOption(voice_name="Erinome", description="クリアるい", sex=Sex.female),
        VoiceOption(voice_name="Algenib", description="ガラガラした", sex=Sex.male),
        VoiceOption(voice_name="Rasalgethi", description="情報に富んでいる", sex=Sex.male),
        VoiceOption(voice_name="Laomedeia", description="アップビート", sex=Sex.female),
        VoiceOption(voice_name="Achernar", description="ソフト", sex=Sex.female),
        VoiceOption(voice_name="Alnilam", description="確実", sex=Sex.male),
        VoiceOption(voice_name="Schedar", description="平らな", sex=Sex.male),
        VoiceOption(voice_name="Gacrux", description="成熟した", sex=Sex.female),
        VoiceOption(voice_name="Pulcherrima", description="前方", sex=Sex.male),
        VoiceOption(voice_name="Achird", description="フレンドリー", sex=Sex.male),
        VoiceOption(voice_name="Zubenelgenubi", description="カジュアル", sex=Sex.male),
        VoiceOption(voice_name="Vindemiatrix", description="優しい", sex=Sex.female),
        VoiceOption(voice_name="Sadachbia", description="生き生きとした", sex=Sex.male),
        VoiceOption(voice_name="Sadaltager", description="知識が豊富", sex=Sex.male),
        VoiceOption(voice_name="Sulafat", description="温かい", sex=Sex.female),
    ]
)
