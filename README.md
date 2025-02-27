# <img src='https://raw.githack.com/FortAwesome/Font-Awesome/master/svgs/solid/robot.svg' card_color='#40DBB0' width='50' height='50' style='vertical-align:bottom'/> OpenAI Persona
 
Give OpenVoiceOS some sass with OpenAI!

Leverages [OpenAI Completions API](https://platform.openai.com/docs/api-reference/completions/create) to create some fun interactions.  Phrases not explicitly handled by other skills will be run by a LLM, so nearly every interaction will have _some_ response.  But be warned, Mycroft might become a bit obnoxious...


## Usage

Spoken answers api with OpenAI completions backend, prompt engineering is used to behave like a voice assistant

```python
from ovos_solver_openai_persona import OpenAIPersonaSolver

bot = OpenAIPersonaSolver({"key": "sk-XXX",
                           "persona": "helpful, creative, clever, and very friendly"})
print(bot.get_spoken_answer("describe quantum mechanics in simple terms"))
# Quantum mechanics is a branch of physics that deals with the behavior of particles on a very small scale, such as atoms and subatomic particles. It explores the idea that particles can exist in multiple states at once and that their behavior is not predictable in the traditional sense.
print(bot.spoken_answer("Quem encontrou o caminho maritimo para o Brazil", {"lang": "pt-pt"}))
# Explorador português Pedro Álvares Cabral é creditado com a descoberta do Brasil em 1500

```
