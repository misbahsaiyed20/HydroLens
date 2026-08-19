"use client";

import { useState, FormEvent } from "react";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api";

type SubmitState = "idle" | "submitting" | "success" | "error";

export default function ReportForm() {
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");
  const [streamName, setStreamName] = useState("");
  const [description, setDescription] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [state, setState] = useState<SubmitState>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  function useMyLocation() {
    if (!navigator.geolocation) {
      setErrorMessage("Geolocation isn't available in this browser.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLatitude(position.coords.latitude.toFixed(6));
        setLongitude(position.coords.longitude.toFixed(6));
      },
      () => setErrorMessage("Couldn't get your location. Enter coordinates manually.")
    );
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setErrorMessage(null);

    if (!image) {
      setErrorMessage("Please attach a photo of the stream.");
      return;
    }

    const formData = new FormData();
    formData.append("latitude", latitude);
    formData.append("longitude", longitude);
    if (streamName) formData.append("stream_name", streamName);
    if (description) formData.append("description", description);
    formData.append("image", image);

    setState("submitting");
    try {
      const response = await fetch(`${API_BASE_URL}/reports`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.detail ? JSON.stringify(body.detail) : "Submission failed.");
      }

      setState("success");
      setStreamName("");
      setDescription("");
      setImage(null);
    } catch (err) {
      setState("error");
      setErrorMessage(err instanceof Error ? err.message : "Something went wrong.");
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-sm font-medium mb-1">Latitude</label>
          <input
            type="number"
            step="any"
            required
            value={latitude}
            onChange={(e) => setLatitude(e.target.value)}
            className="w-full rounded border border-slate-300 px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Longitude</label>
          <input
            type="number"
            step="any"
            required
            value={longitude}
            onChange={(e) => setLongitude(e.target.value)}
            className="w-full rounded border border-slate-300 px-3 py-2 text-sm"
          />
        </div>
      </div>

      <button
        type="button"
        onClick={useMyLocation}
        className="text-sm text-blue-600 hover:underline"
      >
        Use my current location
      </button>

      <div>
        <label className="block text-sm font-medium mb-1">Stream name (optional)</label>
        <input
          type="text"
          value={streamName}
          onChange={(e) => setStreamName(e.target.value)}
          className="w-full rounded border border-slate-300 px-3 py-2 text-sm"
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Description (optional)</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          className="w-full rounded border border-slate-300 px-3 py-2 text-sm"
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Photo</label>
        <input
          type="file"
          accept="image/jpeg,image/png,image/webp"
          required
          onChange={(e) => setImage(e.target.files?.[0] ?? null)}
          className="w-full text-sm"
        />
      </div>

      <button
        type="submit"
        disabled={state === "submitting"}
        className="w-full rounded bg-slate-900 text-white py-2 text-sm font-medium disabled:opacity-50"
      >
        {state === "submitting" ? "Submitting..." : "Submit observation"}
      </button>

      {state === "success" && (
        <p className="text-sm text-green-600">
          Observation submitted. It will be reviewed as part of the evidence pipeline.
        </p>
      )}
      {errorMessage && <p className="text-sm text-red-600">{errorMessage}</p>}
    </form>
  );
}
