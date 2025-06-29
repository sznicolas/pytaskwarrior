FROM python:3.12-bookworm AS twbuilder

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && \
    apt-get install -y \
            build-essential \
            cmake \
            curl \
            git \
            libgnutls28-dev \
            uuid-dev

# Setup language environment
ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8

# Add source directory
ADD . /root/code/
WORKDIR /root/code/


# Setup Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs > rustup.sh && \
    sh rustup.sh -y --profile minimal --default-toolchain stable --component rust-docs &&\
    git clone https://github.com/GothenburgBitFactory/taskwarrior.git &&\
    cd taskwarrior && git checkout stable && cmake -S . -B build -DCMAKE_BUILD_TYPE=Release &&\
    cmake --build build

# COPY --from=twbuilder /root/code/taskwarrior/build/src/task /usr/local/bin
