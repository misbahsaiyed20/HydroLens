"use client";

import { useEffect, useRef, useState, FormEvent, DragEvent } from "react";
import Link from "next/link";
import { Icon } from "@/components/ui/Icon";
import { useAuth } from "@/contexts/AuthContext";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api";

type SubmitState = "idle" | "submitting" | "success" | "error";

export default function ReportForm() {
  const { token, user, loading: authLoading } = useAuth();
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");
  const [streamName, setStreamName] = useState("");
  const [description, setDescription] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [state, setState] = useState<SubmitState>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [submittedId, setSubmittedId] = useState<string | null>(null);
  const [analysisStatus, setAnalysisStatus] = useState<"SUBMITTED" | "ANALYZING" | "ANALYZED" | null>(null);
  const pollCount = useRef(0);

  // Bounded polling so the citizen sees SUBMITTED -> ANALYZING -> ANALYZED
  // without technical jargon. Stops after ANALYZED or 8 tries (~24s) —
  // never polls indefinitely, and failure just leaves the last known
  // status showing rather than erroring the success screen.
  useEffect(() => {
    if (!submittedId || analysisStatus === "ANALYZED" || pollCount.current >= 8 || !token) return;
    const timer = setTimeout(async () => {
      pollCount.current += 1;
      try {
        const res = await fetch(`${API_BASE_URL}/reports/${submittedId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const body = await res.json();
          setAnalysisStatus(body.status);
        }
      } catch {
        // best-effort — polling failure shouldn't disrupt the success screen
      }
    }, 3000);
    return () => clearTimeout(timer);
  }, [submittedId, analysisStatus, token]);

  function setImageFile(file: File | null) {
    setImage(file);
    setPreviewUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return file ? URL.createObjectURL(file) : null;
    });
  }

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

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragActive(false);
    const file = e.dataTransfer.files?.[0];
    if (file) setImageFile(file);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setErrorMessage(null);

    if (!image) {
      setErrorMessage("Please attach a photo of the stream.");
      return;
    }
    if (!token) {
      setErrorMessage("Please log in to submit an observation.");
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
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.detail ? JSON.stringify(body.detail) : "Submission failed.");
      }

      const body = await response.json();
      setSubmittedId(body.id);
      setAnalysisStatus(body.status);
      pollCount.current = 0;
      setState("success");
      setStreamName("");
      setDescription("");
      setImageFile(null);
    } catch (err) {
      setState("error");
      setErrorMessage(err instanceof Error ? err.message : "Something went wrong.");
    }
  }

  if (authLoading) {
    return <div className="py-8 text-center text-xs text-ocean-400">Checking your session…</div>;
  }

  if (!user) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-card border border-ocean-100 bg-ocean-50/60 px-5 py-10 text-center">
        <span className="flex h-11 w-11 items-center justify-center rounded-full bg-white text-ocean-400 shadow-card">
          <Icon.Shield className="h-5 w-5" />
        </span>
        <div>
          <p className="text-sm font-semibold text-ocean-800">Log in to submit an observation</p>
          <p className="mt-1 max-w-xs text-xs leading-relaxed text-ocean-500">
            Reports are tied to your account so you can track their status afterward.
          </p>
        </div>
        <div className="mt-1 flex gap-2">
          <Link href="/login" className="btn-primary">Log in</Link>
          <Link href="/signup" className="btn-secondary">Sign up</Link>
        </div>
      </div>
    );
  }

  if (state === "success") {
    return (
      <div className="flex flex-col items-center gap-3 rounded-card border border-moss-200 bg-moss-50 px-5 py-10 text-center animate-fade-in">
        <span className="flex h-11 w-11 items-center justify-center rounded-full bg-white text-moss-600 shadow-card">
          <Icon.Check className="h-5 w-5" />
        </span>
        <div>
          <p className="text-sm font-semibold text-moss-800">Observation submitted</p>
          <p className="mt-1 max-w-xs text-xs leading-relaxed text-moss-600">
            It now enters the evidence pipeline for analysis and review. Thank you for helping
            watch your stream.
          </p>
          {analysisStatus && (
            <p className="mt-2 text-xs font-medium text-moss-700">
              Status: {analysisStatus === "SUBMITTED" ? "Waiting to be analyzed…" : analysisStatus === "ANALYZING" ? "Analyzing photo…" : "Analyzed"}
            </p>
          )}
        </div>
        <button type="button" className="btn-secondary mt-1" onClick={() => { setState("idle"); setSubmittedId(null); setAnalysisStatus(null); }}>
          Submit another
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Upload area */}
      <div>
        <label className="label-field">Photo</label>
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragActive(true);
          }}
          onDragLeave={() => setDragActive(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed px-4 py-6 text-center transition-colors ${
            dragActive ? "border-aqua-400 bg-aqua-50" : "border-ocean-200 bg-ocean-50/60 hover:border-aqua-300"
          }`}
        >
          {previewUrl ? (
            <div className="flex w-full items-center gap-3">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={previewUrl} alt="Selected observation preview" className="h-16 w-16 rounded-lg object-cover" />
              <div className="flex-1 text-left">
                <div className="truncate text-xs font-medium text-ocean-800">{image?.name}</div>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setImageFile(null);
                    if (fileInputRef.current) fileInputRef.current.value = "";
                  }}
                  className="mt-1 text-xs text-rose-600 hover:underline"
                >
                  Remove
                </button>
              </div>
            </div>
          ) : (
            <>
              <span className="flex h-10 w-10 items-center justify-center rounded-full bg-white text-ocean-400 shadow-card">
                <Icon.Upload className="h-4.5 w-4.5" />
              </span>
              <p className="text-xs font-medium text-ocean-700">Drop a photo here, or tap to choose</p>
              <p className="text-[11px] text-ocean-400">JPEG, PNG or WebP</p>
            </>
          )}
          <input
            ref={fileInputRef}
            id="rf-photo"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            required
            onChange={(e) => setImageFile(e.target.files?.[0] ?? null)}
            className="hidden"
          />
        </div>
      </div>

      {/* Location */}
      <div>
        <div className="mb-1.5 flex items-center justify-between">
          <label className="label-field mb-0">Location</label>
          <button
            type="button"
            onClick={useMyLocation}
            className="flex items-center gap-1 text-xs font-medium text-aqua-600 hover:text-aqua-700"
          >
            <Icon.Pin className="h-3.5 w-3.5" />
            Use my location
          </button>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <input
            id="rf-lat"
            type="number"
            step="any"
            required
            placeholder="Latitude"
            aria-label="Latitude"
            value={latitude}
            onChange={(e) => setLatitude(e.target.value)}
            className="input-field"
          />
          <input
            id="rf-lon"
            type="number"
            step="any"
            required
            placeholder="Longitude"
            aria-label="Longitude"
            value={longitude}
            onChange={(e) => setLongitude(e.target.value)}
            className="input-field"
          />
        </div>
      </div>

      <div>
        <label htmlFor="rf-stream" className="label-field">Stream name <span className="font-normal text-ocean-400">(optional)</span></label>
        <input
          id="rf-stream"
          type="text"
          placeholder="e.g. Willow Creek"
          value={streamName}
          onChange={(e) => setStreamName(e.target.value)}
          className="input-field"
        />
      </div>

      <div>
        <label htmlFor="rf-desc" className="label-field">Description <span className="font-normal text-ocean-400">(optional)</span></label>
        <textarea
          id="rf-desc"
          placeholder="Anything notable — color, smell, foam, dead fish…"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          className="input-field resize-none"
        />
      </div>

      <button type="submit" disabled={state === "submitting"} className="btn-primary w-full">
        {state === "submitting" ? (
          <>
            <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/40 border-t-white" />
            Submitting…
          </>
        ) : (
          <>Submit observation</>
        )}
      </button>

      {errorMessage && (
        <p className="flex items-center gap-1.5 text-sm text-rose-600">
          <Icon.Warning className="h-4 w-4 flex-shrink-0" />
          {errorMessage}
        </p>
      )}
    </form>
  );
}
