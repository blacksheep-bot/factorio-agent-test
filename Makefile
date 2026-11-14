# Convenience wrappers around docker compose + setup/fle_exec.py (see README.md).
# Variables (make VAR=value target, or export them):
#   SCENARIO=open_world|default_lab_scenario  SAVE=<name>  FRESH=1  INVENTORY='{"coal":10}'
#   OUT=render.png X= Y= R=20   NAME=<save name>
COMPOSE ?= docker compose
PY      ?= python3
URL     ?= http://127.0.0.1:$(or $(FLE_REPL_PORT),8765)
OUT     ?= render.png
R       ?= 20
NAME    ?= fle_save
EXEC     = $(PY) setup/fle_exec.py --url $(URL)

export FLE_HOST_ROOT := $(CURDIR)
ifdef SCENARIO
export FLE_SCENARIO := $(SCENARIO)
endif
ifdef SAVE
export FLE_SAVE := $(SAVE)
endif
ifdef FRESH
export FLE_FRESH := $(FRESH)
endif
ifdef INVENTORY
export FLE_INVENTORY := $(INVENTORY)
endif

.PHONY: build up down logs ps status render save load reset shell
build:            ## build both images (first time: ~5-10 min, downloads sprites)
	$(COMPOSE) build
up:               ## start server + REPL (SCENARIO=, SAVE=, FRESH=1, INVENTORY=)
	$(COMPOSE) up -d --build --force-recreate --wait
	@$(EXEC) --status
down:             ## stop and remove the containers (saves in .fle/saves stay)
	$(COMPOSE) down
logs:             ## follow REPL + server logs
	$(COMPOSE) logs -f --tail 50
ps:
	$(COMPOSE) ps
status:
	$(EXEC) --status
render:           ## make render OUT=runs/x/base.png [X=0 Y=0] [R=20]
	$(EXEC) --render $(OUT) --radius $(R) $(if $(X),--x $(X)) $(if $(Y),--y $(Y))
save:             ## make save NAME=mysave  -> .fle/saves/mysave.zip
	$(EXEC) --save $(NAME)
load:             ## make load SAVE=mysave  (restart the stack from .fle/saves/mysave.zip)
	@test -n "$(SAVE)" || { echo "usage: make load SAVE=<name>"; exit 1; }
	$(COMPOSE) up -d --force-recreate --wait
	@$(EXEC) --status
reset:            ## restart from a fresh scenario map (SCENARIO=...), wiping the live world
	FLE_SAVE= FLE_FRESH=1 $(COMPOSE) up -d --force-recreate --wait
	@$(EXEC) --status
shell:            ## python shell in the client container
	$(COMPOSE) exec fle bash
