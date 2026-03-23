import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";

vi.mock("leaflet", () => ({
  default: {
    latLngBounds: vi.fn(() => ({})),
  },
}));

vi.mock("react-leaflet", () => ({
  MapContainer: ({ children }) => <div data-testid="map">{children}</div>,
  TileLayer: () => null,
  CircleMarker: ({ children }) => <div>{children}</div>,
  Popup: ({ children }) => <div>{children}</div>,
  useMap: () => ({
    fitBounds: vi.fn(),
    setView: vi.fn(),
  }),
}));

const mockFires = [
  { lat: 34.05, lon: -118.24, brightness: 360, frp: 55, confidence: "high", risk: 238 },
  { lat: 37.77, lon: -122.42, brightness: 342, frp: 28, confidence: "nominal", risk: 216.4 },
  { lat: 36.17, lon: -115.14, brightness: 330, frp: 16, confidence: "low", risk: 204.4 },
];

beforeEach(() => {
  globalThis.fetch = vi.fn(() =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve(mockFires),
    })
  );
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("App Component", () => {
  it("requests California region by default", async () => {
    render(<App />);
    await screen.findByTestId("events-count");

    expect(globalThis.fetch).toHaveBeenCalled();
    const firstUrl = globalThis.fetch.mock.calls[0][0];
    expect(firstUrl).toContain("/fires");
    expect(firstUrl).toContain("region=ca");
  });

  it("renders legend and event count", async () => {
    render(<App />);

    expect(await screen.findByTestId("legend")).toBeInTheDocument();
    expect(screen.getByTestId("events-count")).toHaveTextContent("3 events");
  });

  it("applies confidence filter to event list", async () => {
    render(<App />);
    await screen.findByTestId("events-count");

    fireEvent.change(screen.getByTestId("confidence-filter"), { target: { value: "high" } });
    expect(screen.getByTestId("events-count")).toHaveTextContent("1 events");
  });

  it("sorts events by FRP ascending", async () => {
    render(<App />);
    await screen.findByTestId("events-count");

    fireEvent.change(screen.getByTestId("sort-key"), { target: { value: "frp" } });
    fireEvent.click(screen.getByTestId("sort-dir"));

    await waitFor(() => {
      const rows = screen.getAllByTestId("event-row");
      expect(rows[0]).toHaveTextContent("FRP: 16");
    });
  });

  it("shows empty-state when filters exclude all events", async () => {
    render(<App />);
    await screen.findByTestId("events-count");

    fireEvent.change(screen.getByTestId("brightness-filter"), { target: { value: "999" } });
    expect(screen.getByText("No events match filters.")).toBeInTheDocument();
    expect(screen.getByTestId("events-count")).toHaveTextContent("0 events");
  });
});

it("can toggle California-only region filter off", async () => {
  render(<App />);
  await screen.findByTestId("events-count");

  fireEvent.click(screen.getByTestId("ca-toggle"));

  await waitFor(() => {
    const latestUrl = globalThis.fetch.mock.calls.at(-1)[0];
    expect(latestUrl).toContain("/fires");
    expect(latestUrl).not.toContain("region=ca");
  });
});

it("shows API error state when backend is unavailable", async () => {
  globalThis.fetch = vi.fn(() =>
    Promise.resolve({
      ok: false,
      status: 500,
      json: () => Promise.resolve({}),
    })
  );

  render(<App />);

  await waitFor(() => {
    expect(screen.getByText(/AI Tracking System Offline/i)).toBeInTheDocument();
  });
});