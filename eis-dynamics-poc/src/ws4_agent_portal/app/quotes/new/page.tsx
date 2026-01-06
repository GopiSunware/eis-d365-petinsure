"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Loader2, Plus, Trash2, CheckCircle } from "lucide-react";
import { api, Driver, Vehicle, CoverageSelection } from "@/lib/api";

const states = [
  "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
  "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
  "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
  "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
  "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
];

const defaultDriver: Driver = {
  first_name: "",
  last_name: "",
  date_of_birth: "",
  gender: "U",
  marital_status: "S",
  license_date: "",
  violations: 0,
  at_fault_accidents: 0,
  is_primary: true,
};

const defaultVehicle: Vehicle = {
  year: 2020,
  make: "",
  model: "",
  body_type: "sedan",
  use: "pleasure",
  annual_miles: 12000,
  anti_theft: false,
  safety_features: [],
};

const defaultCoverages: CoverageSelection[] = [
  { coverage_type: "bodily_injury", limit: 100000, deductible: 0 },
  { coverage_type: "property_damage", limit: 50000, deductible: 0 },
  { coverage_type: "collision", limit: 50000, deductible: 500 },
  { coverage_type: "comprehensive", limit: 50000, deductible: 250 },
];

export default function NewQuotePage() {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    state: "IL",
    zip_code: "",
    drivers: [{ ...defaultDriver }],
    vehicles: [{ ...defaultVehicle }],
    coverages: [...defaultCoverages],
    effective_date: new Date().toISOString().split("T")[0],
    prior_insurance: true,
    homeowner: false,
    multi_policy: false,
  });
  const [quoteResult, setQuoteResult] = useState<any>(null);

  const mutation = useMutation({
    mutationFn: api.getQuote,
    onSuccess: (data) => {
      setQuoteResult(data);
      setStep(4);
    },
  });

  const addDriver = () => {
    setFormData({
      ...formData,
      drivers: [...formData.drivers, { ...defaultDriver, is_primary: false }],
    });
  };

  const removeDriver = (index: number) => {
    if (formData.drivers.length > 1) {
      setFormData({
        ...formData,
        drivers: formData.drivers.filter((_, i) => i !== index),
      });
    }
  };

  const addVehicle = () => {
    setFormData({
      ...formData,
      vehicles: [...formData.vehicles, { ...defaultVehicle }],
    });
  };

  const removeVehicle = (index: number) => {
    if (formData.vehicles.length > 1) {
      setFormData({
        ...formData,
        vehicles: formData.vehicles.filter((_, i) => i !== index),
      });
    }
  };

  const handleSubmit = () => {
    mutation.mutate(formData);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Get a Quote</h1>
        <p className="text-gray-500 mt-1">
          Auto Insurance Premium Calculator
        </p>
      </div>

      {/* Progress Steps */}
      <div className="flex items-center justify-between">
        {["Basic Info", "Drivers", "Vehicles", "Quote"].map((label, index) => (
          <div
            key={label}
            className={`flex items-center ${index < 3 ? "flex-1" : ""}`}
          >
            <div
              className={`h-8 w-8 rounded-full flex items-center justify-center text-sm font-medium ${
                step > index + 1
                  ? "bg-success-500 text-white"
                  : step === index + 1
                  ? "bg-primary-600 text-white"
                  : "bg-gray-200 text-gray-600"
              }`}
            >
              {step > index + 1 ? <CheckCircle className="h-5 w-5" /> : index + 1}
            </div>
            <span
              className={`ml-2 text-sm ${
                step === index + 1 ? "text-primary-600 font-medium" : "text-gray-500"
              }`}
            >
              {label}
            </span>
            {index < 3 && <div className="flex-1 h-px bg-gray-200 mx-4" />}
          </div>
        ))}
      </div>

      {/* Step 1: Basic Info */}
      {step === 1 && (
        <div className="card space-y-6">
          <h2 className="text-lg font-semibold">Basic Information</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">State *</label>
              <select
                className="input"
                value={formData.state}
                onChange={(e) => setFormData({ ...formData, state: e.target.value })}
              >
                {states.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">ZIP Code *</label>
              <input
                type="text"
                className="input"
                placeholder="60601"
                value={formData.zip_code}
                onChange={(e) => setFormData({ ...formData, zip_code: e.target.value })}
              />
            </div>
            <div>
              <label className="label">Effective Date *</label>
              <input
                type="date"
                className="input"
                value={formData.effective_date}
                onChange={(e) => setFormData({ ...formData, effective_date: e.target.value })}
              />
            </div>
          </div>
          <div className="space-y-3">
            <label className="flex items-center">
              <input
                type="checkbox"
                className="h-4 w-4 text-primary-600 rounded"
                checked={formData.prior_insurance}
                onChange={(e) => setFormData({ ...formData, prior_insurance: e.target.checked })}
              />
              <span className="ml-2 text-sm text-gray-700">Currently insured</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                className="h-4 w-4 text-primary-600 rounded"
                checked={formData.homeowner}
                onChange={(e) => setFormData({ ...formData, homeowner: e.target.checked })}
              />
              <span className="ml-2 text-sm text-gray-700">Homeowner</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                className="h-4 w-4 text-primary-600 rounded"
                checked={formData.multi_policy}
                onChange={(e) => setFormData({ ...formData, multi_policy: e.target.checked })}
              />
              <span className="ml-2 text-sm text-gray-700">Bundle with other policies</span>
            </label>
          </div>
          <div className="flex justify-end">
            <button className="btn-primary" onClick={() => setStep(2)}>
              Continue
            </button>
          </div>
        </div>
      )}

      {/* Step 2: Drivers */}
      {step === 2 && (
        <div className="card space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Drivers</h2>
            <button className="btn-secondary flex items-center" onClick={addDriver}>
              <Plus className="h-4 w-4 mr-1" /> Add Driver
            </button>
          </div>
          {formData.drivers.map((driver, index) => (
            <div key={index} className="border border-gray-200 rounded-lg p-4 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-medium">Driver {index + 1} {driver.is_primary && "(Primary)"}</h3>
                {formData.drivers.length > 1 && (
                  <button onClick={() => removeDriver(index)} className="text-danger-600 hover:text-danger-700">
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
              </div>
              <div className="grid grid-cols-2 gap-4">
                <input
                  placeholder="First Name"
                  className="input"
                  value={driver.first_name}
                  onChange={(e) => {
                    const drivers = [...formData.drivers];
                    drivers[index].first_name = e.target.value;
                    setFormData({ ...formData, drivers });
                  }}
                />
                <input
                  placeholder="Last Name"
                  className="input"
                  value={driver.last_name}
                  onChange={(e) => {
                    const drivers = [...formData.drivers];
                    drivers[index].last_name = e.target.value;
                    setFormData({ ...formData, drivers });
                  }}
                />
                <div>
                  <label className="label">Date of Birth</label>
                  <input
                    type="date"
                    className="input"
                    value={driver.date_of_birth}
                    onChange={(e) => {
                      const drivers = [...formData.drivers];
                      drivers[index].date_of_birth = e.target.value;
                      setFormData({ ...formData, drivers });
                    }}
                  />
                </div>
                <div>
                  <label className="label">Date Licensed</label>
                  <input
                    type="date"
                    className="input"
                    value={driver.license_date}
                    onChange={(e) => {
                      const drivers = [...formData.drivers];
                      drivers[index].license_date = e.target.value;
                      setFormData({ ...formData, drivers });
                    }}
                  />
                </div>
                <div>
                  <label className="label">Violations (3 years)</label>
                  <input
                    type="number"
                    min="0"
                    className="input"
                    value={driver.violations}
                    onChange={(e) => {
                      const drivers = [...formData.drivers];
                      drivers[index].violations = parseInt(e.target.value) || 0;
                      setFormData({ ...formData, drivers });
                    }}
                  />
                </div>
                <div>
                  <label className="label">At-Fault Accidents</label>
                  <input
                    type="number"
                    min="0"
                    className="input"
                    value={driver.at_fault_accidents}
                    onChange={(e) => {
                      const drivers = [...formData.drivers];
                      drivers[index].at_fault_accidents = parseInt(e.target.value) || 0;
                      setFormData({ ...formData, drivers });
                    }}
                  />
                </div>
              </div>
            </div>
          ))}
          <div className="flex justify-between">
            <button className="btn-secondary" onClick={() => setStep(1)}>Back</button>
            <button className="btn-primary" onClick={() => setStep(3)}>Continue</button>
          </div>
        </div>
      )}

      {/* Step 3: Vehicles */}
      {step === 3 && (
        <div className="card space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Vehicles</h2>
            <button className="btn-secondary flex items-center" onClick={addVehicle}>
              <Plus className="h-4 w-4 mr-1" /> Add Vehicle
            </button>
          </div>
          {formData.vehicles.map((vehicle, index) => (
            <div key={index} className="border border-gray-200 rounded-lg p-4 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-medium">Vehicle {index + 1}</h3>
                {formData.vehicles.length > 1 && (
                  <button onClick={() => removeVehicle(index)} className="text-danger-600 hover:text-danger-700">
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
              </div>
              <div className="grid grid-cols-3 gap-4">
                <input
                  type="number"
                  placeholder="Year"
                  className="input"
                  value={vehicle.year}
                  onChange={(e) => {
                    const vehicles = [...formData.vehicles];
                    vehicles[index].year = parseInt(e.target.value) || 2020;
                    setFormData({ ...formData, vehicles });
                  }}
                />
                <input
                  placeholder="Make"
                  className="input"
                  value={vehicle.make}
                  onChange={(e) => {
                    const vehicles = [...formData.vehicles];
                    vehicles[index].make = e.target.value;
                    setFormData({ ...formData, vehicles });
                  }}
                />
                <input
                  placeholder="Model"
                  className="input"
                  value={vehicle.model}
                  onChange={(e) => {
                    const vehicles = [...formData.vehicles];
                    vehicles[index].model = e.target.value;
                    setFormData({ ...formData, vehicles });
                  }}
                />
                <select
                  className="input"
                  value={vehicle.body_type}
                  onChange={(e) => {
                    const vehicles = [...formData.vehicles];
                    vehicles[index].body_type = e.target.value;
                    setFormData({ ...formData, vehicles });
                  }}
                >
                  <option value="sedan">Sedan</option>
                  <option value="suv">SUV</option>
                  <option value="truck">Truck</option>
                  <option value="sports">Sports</option>
                  <option value="minivan">Minivan</option>
                </select>
                <select
                  className="input"
                  value={vehicle.use}
                  onChange={(e) => {
                    const vehicles = [...formData.vehicles];
                    vehicles[index].use = e.target.value;
                    setFormData({ ...formData, vehicles });
                  }}
                >
                  <option value="pleasure">Pleasure</option>
                  <option value="commute">Commute</option>
                  <option value="business">Business</option>
                </select>
                <div>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      className="h-4 w-4 text-primary-600 rounded"
                      checked={vehicle.anti_theft}
                      onChange={(e) => {
                        const vehicles = [...formData.vehicles];
                        vehicles[index].anti_theft = e.target.checked;
                        setFormData({ ...formData, vehicles });
                      }}
                    />
                    <span className="ml-2 text-sm">Anti-theft device</span>
                  </label>
                </div>
              </div>
            </div>
          ))}
          <div className="flex justify-between">
            <button className="btn-secondary" onClick={() => setStep(2)}>Back</button>
            <button
              className="btn-primary flex items-center"
              onClick={handleSubmit}
              disabled={mutation.isPending}
            >
              {mutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Calculating...
                </>
              ) : (
                "Get Quote"
              )}
            </button>
          </div>
        </div>
      )}

      {/* Step 4: Quote Result */}
      {step === 4 && quoteResult && (
        <div className="card space-y-6">
          <div className="text-center">
            <CheckCircle className="h-16 w-16 text-success-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-gray-900">Your Quote</h2>
            <p className="text-gray-500">Quote ID: {quoteResult.quote_id}</p>
          </div>

          <div className="bg-primary-50 rounded-lg p-6 text-center">
            <p className="text-sm text-primary-600 mb-1">Total Annual Premium</p>
            <p className="text-4xl font-bold text-primary-700">
              ${quoteResult.premium_breakdown.total_premium.toLocaleString()}
            </p>
            <p className="text-lg text-primary-600 mt-2">
              ${quoteResult.premium_breakdown.monthly_payment.toLocaleString()}/month
            </p>
          </div>

          <div className="space-y-4">
            <h3 className="font-semibold text-gray-900">Premium Breakdown</h3>
            {quoteResult.premium_breakdown.coverage_charges.map((cov: any) => (
              <div key={cov.coverage_type} className="flex justify-between text-sm">
                <span className="text-gray-600 capitalize">
                  {cov.coverage_type.replace("_", " ")}
                </span>
                <span className="font-medium">${cov.final_premium}</span>
              </div>
            ))}
            <div className="border-t pt-4">
              <h4 className="font-medium text-gray-900 mb-2">Discounts Applied</h4>
              {quoteResult.premium_breakdown.discounts_applied.map((disc: any) => (
                <div key={disc.discount_type} className="flex justify-between text-sm text-success-600">
                  <span>{disc.description}</span>
                  <span>-${disc.amount}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="flex justify-center space-x-4">
            <button className="btn-secondary" onClick={() => { setStep(1); setQuoteResult(null); }}>
              New Quote
            </button>
            <button className="btn-primary">Bind Policy</button>
          </div>
        </div>
      )}
    </div>
  );
}
