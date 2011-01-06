version := $(shell python -c "import yaml;d=yaml.load(open('app.yaml')); print d['version']")
dist_dir := dist-$(version)

.PHONY:	all dist bump_version


all:
	@echo "try make bump_version && make dist"


dist:
	@mkdir -p $(dist_dir)
	@cp *.yaml $(dist_dir)
	@cp *.py $(dist_dir)
	@cp apikey.txt $(dist_dir)
	@cp -r simplejson $(dist_dir)
	@cp -r htdocs $(dist_dir)
	@cp -r media $(dist_dir)
	@cp -r tf2apiproxy $(dist_dir)
	@cd $(dist_dir) && appcfg.py update .
	appcfg.py set_default_version .
	git commit -a -m "make dist."
	git tag v$(shell python -c "import yaml;d=yaml.load(open('app.yaml')); print d['version']")


bump_version:
	@python -c "import yaml; d=yaml.load(open('app.yaml')); print 'Old Version', d['version']"
	@python -c "import yaml; d=yaml.load(open('app.yaml')); d['version']+=1; fh = open('app.yaml', 'w'); yaml.dump(d, fh, width=50, indent=4, default_flow_style=False); fh.flush(); fh.close()"
	@python -c "import yaml; d=yaml.load(open('app.yaml')); print 'New Version', d['version']"
