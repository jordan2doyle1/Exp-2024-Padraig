# syntax=docker/dockerfile:1

# INFO: Build context must be parent directory.

FROM python:2

LABEL maintainer "Jordan"

WORKDIR /app

ENV output=/output
RUN mkdir -p $output

ENV task="s-smog"

# RUN apt update && apt install -y software-properties-common
# RUN wget -qO - https://packages.adoptium.net/artifactory/api/gpg/key/public \
#		| apt-key add - && add-apt-repository --y \
#			https://packages.adoptium.net/artifactory/deb
# RUN apt update && apt install -y temurin-8-jdk
# ENV JAVA_HOME=/usr/lib/jvm/temurin-8-jdk-amd64

RUN apt update && apt install -y unzip libglu1

ARG JDK_ARCHIVE="openjdk8.tar.gz"
RUN mkdir -p /usr/lib/jvm
COPY $JDK_ARCHIVE .
RUN tar xzf $JDK_ARCHIVE -C /usr/lib/jvm
ENV JAVA_HOME=/usr/lib/jvm/jdk8u382-b05

ENV ANDROID_HOME="/usr/lib/android-sdk"
RUN mkdir -p $ANDROID_HOME/cmdline-tools

ARG API_LEVEL="28" 
ARG BUILD_VERSION="28.0.3"

ENV PATH="$PATH:$JAVA_HOME/bin"
ENV PATH="$PATH:$ANDROID_HOME/cmdline-tools/tools"
ENV PATH="$PATH:$ANDROID_HOME/cmdline-tools/tools/bin"
ENV PATH="$PATH:$ANDROID_HOME/tools/bin"
ENV PATH="$PATH:$ANDROID_HOME/build-tools/${BUILD_VERSION}"
ENV PATH="$PATH:$ANDROID_HOME/platform-tools"
ENV PATH="$PATH:$ANDROID_HOME/emulator"

ARG CMD_TOOLS_ARCHIVE="commandlinetools-linux-6200805_latest.zip"
ARG EMULATOR_PACKAGE="system-images;android-$API_LEVEL;google_apis;x86"
ARG ANDROID_API="platforms;android-$API_LEVEL"
ARG BUILD_TOOLS="build-tools;$BUILD_VERSION"
ARG SDK_PACKAGES="$EMULATOR_PACKAGE $ANDROID_API $BUILD_TOOLS platform-tools"

ARG TOOLS_BASE_URL="https://dl.google.com/android/repository/"
RUN wget -q "$TOOLS_BASE_URL$CMD_TOOLS_ARCHIVE" -P /tmp
RUN unzip -q -d $ANDROID_HOME/cmdline-tools /tmp/$CMD_TOOLS_ARCHIVE
RUN yes Y | sdkmanager --install $SDK_PACKAGES
RUN yes Y | sdkmanager --licenses
RUN rm /tmp/$CMD_TOOLS_ARCHIVE

ENV EMULATOR_NAME="api28_0"
ENV DEVICE_NAME="Nexus 6"

RUN avdmanager --verbose create avd --force --name "$EMULATOR_NAME" \
		--device "$DEVICE_NAME" --package "$EMULATOR_PACKAGE"

COPY config_device .
COPY log.sh .
RUN ./config_device -c $HOME/.android/avd/$EMULATOR_NAME.avd/config.ini

RUN python -m pip install --upgrade pip
COPY ./$task/requirements.txt .
RUN pip install -r requirements.txt

ENV HOME=/root
RUN mkdir -p acvtool_repo
ADD acvtool_repo ./acvtool_repo
RUN pip install -e acvtool_repo
RUN mkdir -p $HOME/acvtool/
COPY ./$task/config.json $HOME/acvtool/

COPY setting.sh .
COPY util.sh .
COPY acv.sh .
COPY entry_point .

COPY ./$task/ ./

CMD ./entry_point
