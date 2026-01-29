import type { Dispatch, SetStateAction } from "react";

import type { CheckpointStreamData, FullSystemStreamData } from "@/lib/types";

let currentImageURL = "";

const checkpointStreamParser = (
  event: MessageEvent<ArrayBuffer>,
  setCheckpointStreamData: Dispatch<
    SetStateAction<CheckpointStreamData | undefined>
  >,
) => {
  const buffer = event.data;
  const view = new DataView(buffer);

  if (buffer.byteLength < 4) throw new Error("Buffer is less than 4 bytes.");

  const metadataLength = view.getUint32(0, true);
  const metadataStart = 4;
  const metadataEnd = metadataStart + metadataLength;

  if (metadataEnd > buffer.byteLength)
    throw new Error("Metadata length exceeds buffer length.");

  const bufferView = new Uint8Array(buffer);

  const metadataBytes = bufferView.subarray(metadataStart, metadataEnd);
  const metadataString = new TextDecoder("utf-8").decode(metadataBytes);
  const metadata = JSON.parse(metadataString) as CheckpointStreamData;

  const imageBytes = bufferView.subarray(metadataEnd);
  const image = new Blob([imageBytes], { type: "image/jpeg" });

  const newImageURL = URL.createObjectURL(image);
  if (currentImageURL) URL.revokeObjectURL(currentImageURL);

  currentImageURL = newImageURL;

  setCheckpointStreamData({
    imageUrl: newImageURL,
    age: metadata.age,
    weather: metadata.weather,
    timestamp: metadata.timestamp,
  });
};

const fullSystemStreamParser = (
  event: MessageEvent<ArrayBuffer>,
  setFullSystemStreamData: Dispatch<
    SetStateAction<FullSystemStreamData | undefined>
  >,
) => {
  const buffer = event.data;

  const image = new Blob([buffer], { type: "image/jpeg" });

  const newImageURL = URL.createObjectURL(image);
  if (currentImageURL) URL.revokeObjectURL(currentImageURL);

  currentImageURL = newImageURL;

  setFullSystemStreamData({
    imageUrl: newImageURL,
  });
};

export { checkpointStreamParser, fullSystemStreamParser };
