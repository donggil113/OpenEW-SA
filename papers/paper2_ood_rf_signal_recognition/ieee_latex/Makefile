LATEXMK ?= latexmk
MAIN := main

.PHONY: all pdf clean distclean

all: pdf

pdf:
	$(LATEXMK) -pdf -interaction=nonstopmode -halt-on-error -file-line-error $(MAIN).tex

clean:
	$(LATEXMK) -c $(MAIN).tex

distclean:
	$(LATEXMK) -C $(MAIN).tex
