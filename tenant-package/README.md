# Tenant package

The bots, channels, skills and settings for one deployment. The server reads this at startup;
edit it and restart the container to apply changes.

| File | What it defines |
|---|---|
| `agents.yaml` | The bots themselves — each one's name, title, description and instructions. Add a bot by adding an entry. |
| `channels.yaml` | The pre-built channels on the home screen, and which bots may appear in each. |
| `brand.yaml` | The deployment's name and id. |
| `model.yaml` | The model the built-in bots run on (through OpenRouter). |
| `skills.yaml` | The deployment-wide skills: named instructions anyone can invoke with `/`. |
| `knowledge.yaml` | Which document sources the Knowledge bot may search. |

## The vault instruction

Every bot's instructions in `agents.yaml` tell it that its workspace is an Obsidian vault:
plain Markdown notes it can list, read and write, which are its long-term memory. They also
tell it to link notes together with `[[wikilinks]]`, which is what draws the connections in
the vault graph. Keep those lines when you edit the prompts — they are what makes the vault
and the graph fill up with real work.
