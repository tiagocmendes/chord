# CHORD (DHT)

This repository implements a simple version of the [CHORD](https://en.wikipedia.org/wiki/Chord_(peer-to-peer)) algorithm.
The provided code already setups the ring network properly.
1. Supports Node Joins
2. Finds the correct successor for a node
3. Run Stabilize periodically to correct the network


## Running the example
Run in two different terminal:

DHT (setups a CHORD DHT):
```console
$ python3 DHT.py
```
example (put and get objects from the DHT):
```console
$ python3 example.py
```

## Useful links
Work objectives: [CD2019G03.pdf](https://github.com/detiuaveiro/chord-tiagocmendes/blob/master/CD2019G03.pdf)  

[Chord: A scalable peer-to-peer lookup service for inter-net applications](https://pdos.csail.mit.edu/papers/chord:sigcomm01/chord_sigcomm.pdf)

[https://en.wikipedia.org/wiki/Chord_(peer-to-peer)](https://en.wikipedia.org/wiki/Chord_(peer-to-peer))

## Authors

* **Mário Antunes** - [mariolpantunes](https://github.com/mariolpantunes)
* **Tiago Mendes** - [tiagocmendes](https://github.com/tiagocmendes)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
