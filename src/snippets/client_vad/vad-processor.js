/**
 * VAD Processor
 */

class VADProcessor extends AudioWorkletProcessor {
    constructor() {
      super();
      // Set a threshold for voice detection – you may need to adjust this based on your environment.
      this.threshold = 0.05;
    }
  
    process(inputs, outputs, parameters) {
      // inputs is an array of input channels, we assume mono input here
      const input = inputs[0];
      if (input && input.length > 0) {
        const channelData = input[0];
        let sum = 0;
        // Compute the RMS of the input buffer
        for (let i = 0; i < channelData.length; i++) {
          sum += channelData[i] ** 2;
        }
        const rms = Math.sqrt(sum / channelData.length);
  
        // Post a message if voice is detected or not
        if (rms > this.threshold) {
          this.port.postMessage({ voice: true, rms: rms });
        } else {
          this.port.postMessage({ voice: false, rms: rms });
        }
      }
      // Returning true keeps the processor alive.
      return true;
    }
  }
  
  registerProcessor('vad-processor', VADProcessor);
  