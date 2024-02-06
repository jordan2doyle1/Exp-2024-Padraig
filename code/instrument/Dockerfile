# syntax=docker/dockerfile:1

# INFO: Build context must be parent directory.

FROM openjdk:8

LABEL maintainer "Jordan"

WORKDIR /app

ENV output=/output
RUN mkdir -p $output

ENV task="instrument"
ENV multiple_runs=false

ENV ANDROID_HOME=/usr/lib/android-sdk
RUN mkdir -p $ANDROID_HOME/cmdline-tools

RUN apt update && apt install -y unzip

ARG API_LEVEL="29"
ARG BUILD_VERSION="29.0.3"

ARG CMD_TOOLS_ARCHIVE="commandlinetools-linux-6200805_latest.zip"
ARG ANDROID_API="platforms;android-$API_LEVEL"
ARG BUILD_TOOLS="build-tools;$BUILD_VERSION"
ARG SDK_PACKAGES="$ANDROID_API $BUILD_TOOLS platform-tools"

ENV PATH="$PATH:$ANDROID_HOME/cmdline-tools/tools"
ENV PATH="$PATH:$ANDROID_HOME/cmdline-tools/tools/bin"
ENV PATH="$PATH:$ANDROID_HOME/tools/bin"
ENV PATH="$PATH:$ANDROID_HOME/build-tools/${BUILD_VERSION}"
ENV PATH="$PATH:$ANDROID_HOME/platform-tools"

ARG TOOLS_BASE_URL="https://dl.google.com/android/repository/"
RUN wget -q "$TOOLS_BASE_URL$CMD_TOOLS_ARCHIVE" -P /tmp
RUN unzip -q -d $ANDROID_HOME/cmdline-tools /tmp/$CMD_TOOLS_ARCHIVE
RUN yes Y | sdkmanager --install $SDK_PACKAGES
RUN yes Y | sdkmanager --licenses
RUN rm /tmp/$CMD_TOOLS_ARCHIVE

COPY log.sh .
COPY setting.sh .
COPY util.sh .
COPY entry_point .

COPY ./$task/* ./

CMD ./entry_point
