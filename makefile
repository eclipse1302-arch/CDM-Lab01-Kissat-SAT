COURSESATBUILD=/mnt/e/SJTU/Learning/1.1/CDM/LAB01/build
all:
	$(MAKE) -C "$(COURSESATBUILD)"
clean:
	@if [ -d "$(COURSESATBUILD)" ]; \
	then \
	  if [ -f "$(COURSESATBUILD)"/makefile ]; \
	  then \
	     touch "$(COURSESATBUILD)"/build.hpp; \
	     $(MAKE) -C "$(COURSESATBUILD)" clean; \
	  fi; \
	  rm -rf "$(COURSESATBUILD)"; \
	fi
	rm -f "/mnt/e/SJTU/Learning/1.1/CDM/LAB01/src/makefile"
	rm -f "/mnt/e/SJTU/Learning/1.1/CDM/LAB01/makefile"
test:
	$(MAKE) -C "$(COURSESATBUILD)" test
part1_test:
	$(MAKE) -C "$(COURSESATBUILD)" part1_test
part2_test:
	$(MAKE) -C "$(COURSESATBUILD)" part2_test

public_test:
	$(MAKE) -C "$(COURSESATBUILD)" public_test

handin:
	$(MAKE) -C "$(COURSESATBUILD)" handin
coursesat:
	$(MAKE) -C "$(COURSESATBUILD)" coursesat
format:
	$(MAKE) -C "$(COURSESATBUILD)" format
.PHONY: all coursesat clean test format part1_test part2_test public_test handin
