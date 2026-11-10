class MicProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.ratio = sampleRate / 16000; // sampleRate = mic's native rate
    this.phase = 0;
    this.acc = 0;
    this.count = 0;
    this.out = [];
  }

  process(inputs) {
    const channel = inputs[0][0];
    if (!channel) return true;

    for (let i = 0; i < channel.length; i++) {
      this.acc += channel[i];
      this.count++;
      this.phase += 1;
      if (this.phase >= this.ratio) {
        this.phase -= this.ratio;
        this.out.push(this.acc / this.count);
        this.acc = 0;
        this.count = 0;

        if (this.out.length >= 1600) { // 100 ms at 16 kHz
          const int16 = new Int16Array(this.out.length);
          for (let j = 0; j < this.out.length; j++) {
            const s = Math.max(-1, Math.min(1, this.out[j]));
            int16[j] = s < 0 ? s * 0x8000 : s * 0x7fff;
          }
          this.port.postMessage(int16.buffer, [int16.buffer]);
          this.out = [];
        }
      }
    }
    return true;
  }
}

registerProcessor("mic-processor", MicProcessor);
