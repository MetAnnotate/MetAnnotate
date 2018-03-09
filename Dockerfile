FROM linuxbrew/linuxbrew:1.5.5
LABEL maintainer="Jackson M. Tsuji <jackson.tsuji@uwaterloo.ca>"

# Install dependencies
RUN sudo apt-get update \
	&& sudo apt-get install -y python-dev

# Copy the repo (excludes .dockerignore)
COPY . /home/linuxbrew/Metannotate

# Install MetAnnotate (command line) and test
RUN bash /home/linuxbrew/Metannotate/base_installation.sh
RUN bash /home/linuxbrew/Metannotate/testing/test_metannotate_end_to_end.sh
ENV PATH="${PATH}:/home/linuxbrew/Metannotate"

ENTRYPOINT /bin/bash
