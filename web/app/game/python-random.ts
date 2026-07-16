/** Python-compatible integer-seeded MT19937 subset used by random.Random(seed). */
export class PythonRandom {
  private state = new Uint32Array(624);
  private index = 624;

  constructor(seed: number) { this.seed(seed); }

  private initGenRand(seed: number) {
    this.state[0] = seed >>> 0;
    for (let i = 1; i < 624; i++) {
      const prior = this.state[i - 1] ^ (this.state[i - 1] >>> 30);
      this.state[i] = (Math.imul(1812433253, prior) + i) >>> 0;
    }
    this.index = 624;
  }

  private seed(value: number) {
    const absolute = BigInt(Math.abs(Math.trunc(value)));
    const key: number[] = [];
    let remaining = absolute;
    do { key.push(Number(remaining & 0xffffffffn)); remaining >>= 32n; } while (remaining);
    this.initGenRand(19650218);
    let i = 1, j = 0;
    for (let k = Math.max(624, key.length); k; k--) {
      const prior = this.state[i - 1] ^ (this.state[i - 1] >>> 30);
      this.state[i] = ((this.state[i] ^ Math.imul(prior, 1664525)) + key[j] + j) >>> 0;
      i++; j++; if (i >= 624) { this.state[0] = this.state[623]; i = 1; } if (j >= key.length) j = 0;
    }
    for (let k = 623; k; k--) {
      const prior = this.state[i - 1] ^ (this.state[i - 1] >>> 30);
      this.state[i] = ((this.state[i] ^ Math.imul(prior, 1566083941)) - i) >>> 0;
      i++; if (i >= 624) { this.state[0] = this.state[623]; i = 1; }
    }
    this.state[0] = 0x80000000;
  }

  private twist() {
    for (let i = 0; i < 624; i++) {
      const y = (this.state[i] & 0x80000000) | (this.state[(i + 1) % 624] & 0x7fffffff);
      this.state[i] = this.state[(i + 397) % 624] ^ (y >>> 1) ^ ((y & 1) ? 0x9908b0df : 0);
    }
    this.index = 0;
  }

  private uint32() {
    if (this.index >= 624) this.twist();
    let y = this.state[this.index++];
    y ^= y >>> 11; y ^= (y << 7) & 0x9d2c5680; y ^= (y << 15) & 0xefc60000; y ^= y >>> 18;
    return y >>> 0;
  }

  random() { const a = this.uint32() >>> 5; const b = this.uint32() >>> 6; return (a * 67108864 + b) / 9007199254740992; }
  uniform(low: number, high: number) { return low + (high - low) * this.random(); }
}

