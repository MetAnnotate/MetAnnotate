FROM linuxbrew/linuxbrew:1.5.5
LABEL maintainer="Jackson M. Tsuji <jackson.tsuji@uwaterloo.ca>"

RUN sudo apt-get update \
	&& sudo apt-get install -y python-dev

RUN git clone -b linuxbrew https://github.com/Metannotate/Metannotate.git /home/linuxbrew/Metannotate \
	&& cd /home/linuxbrew/Metannotate \
	&& bash base_installation.sh \
	
RUN bash testing/test_metannotate_end_to_end.sh

ENV PATH="${PATH}:/home/linuxbrew/Metannotate"

ENTRYPOINT /bin/bash
