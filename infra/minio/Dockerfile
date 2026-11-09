FROM golang:latest AS build
RUN go install github.com/minio/minio@latest

FROM debian:bookworm-slim
COPY --from=build /go/bin/minio /usr/local/bin/minio
EXPOSE 9000 9001
ENTRYPOINT ["minio"]
