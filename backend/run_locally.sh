#!/bin/bash

docker build -t ekiden .

docker run -p 8080:8080 -v .:/app ekiden
