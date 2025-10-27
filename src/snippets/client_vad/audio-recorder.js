/**
 * Audio Recorder Worklet
 */

import { arrayBufferToBase64 } from './shared.js';
import { eventBus } from './event-bus.js';
let stream;
let isSilence = true;
let lastTimeVoiceActivated = 0;
let sentSamples = 0;
const SILENCE_PERIOD = 2000;

// Audio buffering variables
let audioBuffer = [];
let bufferDuration = 0.5; // 0.5 seconds
let sampleRate = 16000; // Will be set from context
let bufferSize = 0; // Will be calculated
let currentBufferLength = 0;

// Attempt to create an AudioContext with a sample rate of 16000 Hz.
const audioRecorderContext = new AudioContext({ sampleRate: 16000 });


export async function startAudioRecorderWorklet(audioRecorderHandler) {

  // Initialize buffering parameters
  sampleRate = audioRecorderContext.sampleRate;
  bufferSize = bufferDuration * sampleRate;
  console.log(`Audio buffering initialized: ${bufferDuration}s buffer, ${sampleRate}Hz sample rate, ${bufferSize} samples per buffer`);

  // Load the AudioWorklet module.
  const workletURL = new URL('./pcm-recorder-processor.js', import.meta.url);

  await audioRecorderContext.audioWorklet.addModule(workletURL);

  // Request access to the microphone.
  const media_stream_constraints = { audio: { channelCount: 1 } };
  stream = await navigator.mediaDevices.getUserMedia(media_stream_constraints);
  const source = audioRecorderContext.createMediaStreamSource(stream);
  console.log("audioRecorderContext created", workletURL);

  // Create an AudioWorkletNode that uses the PCMProcessor.
  const audioRecorderNode = new AudioWorkletNode(
    audioRecorderContext,
    "pcm-recorder-processor"
  );

  // Connect the microphone source to the worklet.
  source.connect(audioRecorderNode);
  audioRecorderNode.port.onmessage = (event) => {

    const inputData = event.data;
    
    // Add samples to buffer
    audioBuffer.push(...inputData);
    currentBufferLength += inputData.length;

    // Check if we have enough samples for 0.5 seconds AND voice is detected
    if (currentBufferLength >= bufferSize && !isSilence) {
      // Extract exactly 0.5 seconds worth of samples
      const bufferToSend = new Float32Array(bufferSize);
      for (let i = 0; i < bufferSize; i++) {
        bufferToSend[i] = audioBuffer[i];
      }

      // Convert to 16-bit PCM
      const pcmData = convertFloat32ToPCM(bufferToSend);

      // Wrap the pcm data with a JSON message with base64
      const messageJson = JSON.stringify({
        mime_type: "audio/pcm",
        data: arrayBufferToBase64(pcmData),
      });

      eventBus.emit('audio-recorder-message');

      // Send the JSON message to the handler
      audioRecorderHandler(messageJson);

      // Remove the sent samples from the buffer
      audioBuffer = audioBuffer.slice(bufferSize);
      currentBufferLength -= bufferSize;
      
      console.log(`Sent 0.5s buffer with ${bufferSize} samples, remaining buffer: ${currentBufferLength} samples`);
    }
    
    // Clear buffer if we're in silence to prevent buildup
    if (isSilence && currentBufferLength > bufferSize * 2) {
      audioBuffer = [];
      currentBufferLength = 0;
      console.log("Cleared audio buffer due to silence");
    }

  };

  // Load the VAD processor module
  const vadWorkletURL = new URL('./vad-processor.js', import.meta.url);
  audioRecorderContext.audioWorklet.addModule(vadWorkletURL).then(() => {
    // Create an instance of the AudioWorkletNode using your processor
    const vadNode = new AudioWorkletNode(audioRecorderContext, 'vad-processor');

    // Listen for messages from the processor (voice detected or not)
    vadNode.port.onmessage = event => {
      const { voice, rms } = event.data;
      if (voice) {
        if (isSilence) console.log("Voice detected.");
        isSilence = false;
        lastTimeVoiceActivated = new Date();
        sentSamples = 0;
      } else {
        if (new Date() - lastTimeVoiceActivated > SILENCE_PERIOD) {
          const samplesPerSec = sentSamples / ((new Date() - lastTimeVoiceActivated) / 1000);
          if (!isSilence) console.log("Voice stopped. " + samplesPerSec.toFixed(2) + " samples/s");
          isSilence = true;
        }
      }
    };
    // Connect the microphone source to the VAD processor
    source.connect(vadNode);
  });

  return [audioRecorderNode, audioRecorderContext, stream];
}

// Convert Float32 samples to 16-bit PCM.
function convertFloat32ToPCM(inputData) {
  // Create an Int16Array of the same length.
  const pcm16 = new Int16Array(inputData.length);
  for (let i = 0; i < inputData.length; i++) {
    // Multiply by 0x7fff (32767) to scale the float value to 16-bit PCM range.
    pcm16[i] = inputData[i] * 0x7fff;
  }
  sentSamples += inputData.length;
  // Return the underlying ArrayBuffer.
  return pcm16.buffer;
}

/**
 * Stop the microphone.
 */
export function stopMicrophone(micStream) {
  stream.getTracks().forEach(track => track.stop());
  console.log("stopMicrophone(): Microphone stopped.");
}
