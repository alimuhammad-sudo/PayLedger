import { afterEach, describe, expect, it, vi } from "vitest";

import { api, ApiError, toApiError, toQuery } from "@/lib/api";

describe("toQuery", () => {
  it("drops empty values", () => {
    expect(toQuery({ search: "", country: "GB", page: 2, level: undefined })).toBe(
      "?country=GB&page=2",
    );
    expect(toQuery({})).toBe("");
  });
});

describe("toApiError", () => {
  it("keeps our per-field messages", () => {
    const err = toApiError(422, {
      message: "Please fix the highlighted fields",
      fields: { new_salary: "is the same as the current salary" },
    });
    expect(err.status).toBe(422);
    expect(err.fields).toEqual({ new_salary: "is the same as the current salary" });
  });

  it("maps FastAPI validation errors to the field name", () => {
    const err = toApiError(422, { detail: [{ loc: ["body", "email"], msg: "not a valid email" }] });
    expect(err.fields).toEqual({ email: "not a valid email" });
  });

  it("explains a network failure", () => {
    expect(toApiError(0, null).message).toBe("Cannot reach the server.");
  });
});

describe("api", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("calls the same-origin proxy with the cookie and JSON body", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ ok: true })));
    vi.stubGlobal("fetch", fetchMock);

    await api("/employees/3/salary-changes", { method: "POST", body: { new_salary: "1" } });

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/employees/3/salary-changes");
    expect(init.credentials).toBe("same-origin");
    expect(init.headers).toEqual({ "Content-Type": "application/json" });
    expect(JSON.parse(init.body)).toEqual({ new_salary: "1" });
  });

  it("throws ApiError with the server's message", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ message: "Only HR admins can make changes." }), { status: 403 }),
    ));
    await expect(api("/employees")).rejects.toEqual(
      expect.objectContaining({ status: 403, message: "Only HR admins can make changes." }),
    );
    await expect(api("/employees")).rejects.toBeInstanceOf(ApiError);
  });

  it("returns nothing for 204", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status: 204 })));
    await expect(api("/auth/logout", { method: "POST" })).resolves.toBeUndefined();
  });
});
