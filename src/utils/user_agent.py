from pathlib import Path
from typing import Literal
import json, os, sys


def get_user_agent(browser:Literal['chrome', 'edge', 'safari', 'firefox']="chrome") -> str:
    with Path(os.path.realpath(__file__)).with_name("user_agents.json").open() as f:
        user_agents = json.load(f)
    
    if user_agents.get(sys.platform):
        return user_agents[sys.platform][browser]["user_agent"]
    
    if sys.platform == "cygwin":
        return user_agents["windows"][browser]["user_agent"]
    
    else:
        return user_agents["linux"][browser]["user_agent"]
