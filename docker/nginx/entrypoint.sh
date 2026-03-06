#!/bin/sh

export DNS_SERVER=$(cat /etc/resolv.conf  | grep -v '^#' | grep nameserver | awk '{print $2}')

sed -e "s/{DNS_SERVER}/$DNS_SERVER/" -e "s/{NODE_DNS}/$NODE_DNS/" /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf && \

nginx -g 'daemon off;'
