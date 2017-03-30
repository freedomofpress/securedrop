FROM node
MAINTAINER William Budington <bill@eff.org>

WORKDIR /opt

COPY package.json .
RUN npm install
COPY index.js .
COPY config.json.example .
RUN mv config.json.example config.json

CMD ["node", "index.js"]
