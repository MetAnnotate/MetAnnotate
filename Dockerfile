# MetAnnotate command-line Dockerfile

# Build and push to Docker Hub with:
# docker build --no-cache -t jmtsuji/metannotate:0.9.0 -t jmtsuji/metannotate:latest https://github.com/Metannotate/Metannotate.git#0.9.0
# docker push jmtsuji/metannotate

FROM linuxbrew/linuxbrew:1.5.5
LABEL maintainer="Jackson M. Tsuji <jackson.tsuji@uwaterloo.ca>"

# Install dependencies
RUN sudo apt-get update \
	&& sudo apt-get install -y python-dev

# Clone the repo
RUN git clone -b linuxbrew https://github.com/Metannotate/Metannotate.git /home/linuxbrew/Metannotate

# Install MetAnnotate (command line) and test
RUN cd /home/linuxbrew/Metannotate && bash base_installation.sh
RUN cd /home/linuxbrew/Metannotate && bash testing/test_metannotate_end_to_end.sh
ENV PATH="${PATH}:/home/linuxbrew/Metannotate"
