# MetAnnotate command-line Dockerfile

# Build and push to Docker Hub with:
# docker build --no-cache -t metannotate/metannotate:0.9.2 -t metannotate/metannotate:latest https://github.com/metannotate/metannotate.git#0.9.2
# docker push metannotate/metannotate

FROM linuxbrew/linuxbrew:1.5.5
LABEL maintainer="Jackson M. Tsuji <jackson.tsuji@uwaterloo.ca>"

# Install dependencies
RUN sudo apt-get update \
	&& sudo apt-get install -y python-dev

# Clone the repo
RUN git clone -b 0.9.2 https://github.com/metannotate/metannotate.git /home/linuxbrew/MetAnnotate

# Install MetAnnotate (command line) and test
RUN cd /home/linuxbrew/MetAnnotate && bash base_installation.sh
RUN cd /home/linuxbrew/MetAnnotate && bash testing/test_metannotate_end_to_end.sh
ENV PATH="${PATH}:/home/linuxbrew/MetAnnotate"
ENV METANNOTATE_DIR="/home/linuxbrew/MetAnnotate"
