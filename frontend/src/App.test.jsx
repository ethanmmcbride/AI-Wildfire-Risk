import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";

vi.mock("leaflet", () => ({
  default: {
    latLngBounds: vi.fn(() => ({})),
    heatLayer: vi.fn(() => ({
      addTo: vi.fn(),
      remove: vi.fn(),
    })),
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

vi.mock("react-leaflet-markercluster", () => ({
  default: ({ children }) => <div>{children}</div>,
}));

vi.mock("leaflet.heat", () => ({}));

const mockFires = [
  { lat: 34.05, lon: -118.24, brightness: 360, frp: 55, confidence: "high", risk: 0.92 },
  { lat: 37.77, lon: -122.42, brightness: 342, frp: 28, confidence: "nominal", risk: 0.65 },
  { lat: 36.17, lon: -115.14, brightness: 330, frp: 16, confidence: "low", risk: 0.41 },
];

const mockHealth = { status: "ok", model_loaded: true, model_path: "/path/to/model.joblib" };

beforeEach(() => {
  globalThis.fetch = vi.fn((url) => {
    if (String(url).includes("/health")) {
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockHealth),
      });
    }
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve(mockFires),
    });
  });
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("App Component", () => {
  it("requests California region by default", async () => {
    render(<App />);
    await screen.findByTestId("events-count");

    expect(globalThis.fetch).toHaveBeenCalled();
    const firesCalls = globalThis.fetch.mock.calls.filter((c) => String(c[0]).includes("/fires"));
    expect(firesCalls.length).toBeGreaterThan(0);
    expect(firesCalls[0][0]).toContain("region=ca");
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

  it("can switch region to All US", async () => {
    render(<App />);
    await screen.findByTestId("events-count");

    fireEvent.change(screen.getByTestId("region-filter"), { target: { value: "us" } });

    await waitFor(() => {
      const firesCalls = globalThis.fetch.mock.calls.filter((c) => String(c[0]).includes("/fires"));
      const latestUrl = firesCalls.at(-1)[0];
      expect(latestUrl).toContain("/fires");
      expect(latestUrl).not.toContain("region=");
    });
  });

  it("can switch region to Florida", async () => {
    render(<App />);
    await screen.findByTestId("events-count");

    fireEvent.change(screen.getByTestId("region-filter"), { target: { value: "fl" } });

    await waitFor(() => {
      const firesCalls = globalThis.fetch.mock.calls.filter((c) => String(c[0]).includes("/fires"));
      const latestUrl = firesCalls.at(-1)[0];
      expect(latestUrl).toContain("region=fl");
    });
  });

  it("shows model status indicator", async () => {
    render(<App />);
    await screen.findByTestId("events-count");

    await waitFor(() => {
      expect(screen.getByTestId("model-status")).toHaveTextContent("AI Model");
    });
  });

  it("shows fallback status when model is not loaded", async () => {
    globalThis.fetch = vi.fn((url) => {
      if (String(url).includes("/health")) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ status: "ok", model_loaded: false }),
        });
      }
      return Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockFires),
      });
    });

    render(<App />);
    await screen.findByTestId("events-count");

    await waitFor(() => {
      expect(screen.getByTestId("model-status")).toHaveTextContent("Fallback");
    });
  });
});
