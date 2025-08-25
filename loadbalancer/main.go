package main

import (
	"fmt"
	"log"
	"net/url"
	"sync/atomic"
)

type Backend struct {
	URL   *url.URL
	alive bool
	// ReverseProxy *httputil.ReverseProxy
}

type LoadBalancer struct {
	backends []*Backend // slice/vector of pointers to Backend structs
	current  uint64
}

func NewLoadBalancer(backends []*Backend) *LoadBalancer {
	return &LoadBalancer{
		backends: make([]*Backend, 0),
	}
}

func (lb *LoadBalancer) AddBackend(urlStr string) error {
	u, err := url.Parse(urlStr)
	if err != nil {
		return err
	}

	backend := &Backend{
		URL:   u,
		alive: true,
	}

	lb.backends = append(lb.backends, backend)
	log.Printf("Added backend: %s\n", urlStr)
	return nil
}

func (lb *LoadBalancer) NextBackend() *Backend {
	if len(lb.backends) == 0 {
		return nil
	}

	next := atomic.AddUint64(&lb.current, 1)
}

func main() {
	fmt.Println("Hello, world")

}
