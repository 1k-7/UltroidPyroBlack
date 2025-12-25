# Ultroid - UserBot
# Copyright (C) 2021-2025 TeamUltroid
# Rewritten for Pyroblack by Gemini

from . import get_help

__doc__ = get_help("help_calculator")

from . import ultroid_cmd

@ultroid_cmd(pattern="calc( (.*)|$)")
async def _(event):
    match = event.matches[0].group(1).strip() if event.matches else None
    if not match:
        return await event.eor("`Give me an expression to calculate!`")
        
    try:
        # Safe eval logic or just basic python eval
        # Allowing standard math functions
        safe_dict = {
            "abs": abs, "round": round, "min": min, "max": max,
            "pow": pow, "len": len, "sum": sum, "int": int, "float": float
        }
        # Be careful with eval in userbots, but standard for calculator plugins
        result = eval(match, {"__builtins__": None}, safe_dict)
        await event.eor(f"**Expression:** `{match}`\n**Result:** `{result}`")
    except Exception as e:
        await event.eor(f"**Error:** `{e}`")
