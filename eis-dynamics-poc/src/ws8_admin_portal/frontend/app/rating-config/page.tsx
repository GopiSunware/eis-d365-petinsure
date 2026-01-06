'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Calculator, Save, AlertCircle, Plus } from 'lucide-react';
import { ratingConfigApi } from '@/lib/api';
import { formatCurrency } from '@/lib/utils';
import type { RatingFactorsConfig } from '@/lib/types';

export default function RatingConfigPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'base' | 'breed' | 'age' | 'geo' | 'calc'>('base');
  const [changeReason, setChangeReason] = useState('');
  const [hasChanges, setHasChanges] = useState(false);
  const [formData, setFormData] = useState<any>({});

  // Calculator state
  const [calcParams, setCalcParams] = useState({
    species: 'dog',
    breed: 'Labrador Retriever',
    age_years: 3,
    region: 'midwest',
    plan: 'comprehensive',
    deductible: 250,
    reimbursement_percent: 80,
  });
  const [calcResult, setCalcResult] = useState<any>(null);

  const { data: config, isLoading } = useQuery<RatingFactorsConfig>({
    queryKey: ['ratingConfig'],
    queryFn: ratingConfigApi.get,
  });

  const updateMutation = useMutation({
    mutationFn: (data: { config: any; reason: string }) =>
      ratingConfigApi.update(data.config, data.reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ratingConfig'] });
      setHasChanges(false);
      setChangeReason('');
      setFormData({});
      alert('Configuration change submitted for approval');
    },
  });

  const handleCalculate = async () => {
    try {
      const result = await ratingConfigApi.calculatePremium(calcParams);
      setCalcResult(result);
    } catch (error) {
      console.error('Calculation failed:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  const currentConfig = {
    base_rates: { ...config?.base_rates, ...formData.base_rates },
    breed_multipliers: config?.breed_multipliers,
    age_factors: { ...config?.age_factors, ...formData.age_factors },
    geographic_factors: config?.geographic_factors,
    discounts: { ...config?.discounts, ...formData.discounts },
  };

  const handleBaseRateChange = (species: string, value: number) => {
    setFormData((prev: any) => ({
      ...prev,
      base_rates: { ...prev.base_rates, [species]: value },
    }));
    setHasChanges(true);
  };

  const handleSubmit = () => {
    if (changeReason.length < 10) {
      alert('Please provide a change reason (at least 10 characters)');
      return;
    }
    updateMutation.mutate({ config: formData, reason: changeReason });
  };

  const tabs = [
    { id: 'base', label: 'Base Rates' },
    { id: 'breed', label: 'Breed Factors' },
    { id: 'age', label: 'Age Factors' },
    { id: 'geo', label: 'Geographic' },
    { id: 'calc', label: 'Calculator' },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Rating Factors</h1>
        <p className="text-slate-500">Configure premium calculation parameters</p>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <nav className="flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab.id
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {activeTab === 'base' && (
            <div className="card">
              <div className="card-header">
                <h2 className="font-semibold text-slate-900">Base Monthly Rates</h2>
              </div>
              <div className="card-body">
                <div className="grid grid-cols-2 gap-4">
                  {['dog', 'cat', 'bird', 'exotic'].map((species) => (
                    <div key={species} className="p-4 bg-slate-50 rounded-lg">
                      <label className="label capitalize">{species}</label>
                      <div className="flex items-center">
                        <span className="text-slate-500 mr-2">$</span>
                        <input
                          type="number"
                          className="input w-32"
                          step="0.01"
                          value={currentConfig.base_rates?.[species as keyof typeof currentConfig.base_rates] || 0}
                          onChange={(e) => handleBaseRateChange(species, parseFloat(e.target.value))}
                        />
                        <span className="text-slate-500 ml-2">/month</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'breed' && (
            <div className="card">
              <div className="card-header flex items-center justify-between">
                <h2 className="font-semibold text-slate-900">Breed Multipliers</h2>
              </div>
              <div className="card-body">
                <div className="mb-6">
                  <h3 className="font-medium text-slate-700 mb-3">Dogs</h3>
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Breed</th>
                        <th>Risk Category</th>
                        <th>Multiplier</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(config?.breed_multipliers?.dogs || []).map((breed) => (
                        <tr key={breed.breed_name}>
                          <td>{breed.breed_name}</td>
                          <td>
                            <span className={`badge-${breed.risk_category === 'high' ? 'danger' : breed.risk_category === 'medium' ? 'warning' : 'success'}`}>
                              {breed.risk_category}
                            </span>
                          </td>
                          <td>{breed.multiplier}x</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div>
                  <h3 className="font-medium text-slate-700 mb-3">Cats</h3>
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Breed</th>
                        <th>Risk Category</th>
                        <th>Multiplier</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(config?.breed_multipliers?.cats || []).map((breed) => (
                        <tr key={breed.breed_name}>
                          <td>{breed.breed_name}</td>
                          <td>
                            <span className={`badge-${breed.risk_category === 'high' ? 'danger' : breed.risk_category === 'medium' ? 'warning' : 'success'}`}>
                              {breed.risk_category}
                            </span>
                          </td>
                          <td>{breed.multiplier}x</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'age' && (
            <div className="card">
              <div className="card-header">
                <h2 className="font-semibold text-slate-900">Age Factors</h2>
              </div>
              <div className="card-body">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Age Range</th>
                      <th>Factor</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(config?.age_factors?.ranges || {}).map(([range, factor]) => (
                      <tr key={range}>
                        <td>{range} years</td>
                        <td>{factor}x</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                <div className="mt-4 p-4 bg-slate-50 rounded-lg">
                  <p className="text-sm text-slate-600">
                    <strong>Senior Surcharge:</strong> {config?.age_factors?.senior_surcharge_percent}%
                    applied starting at age {config?.age_factors?.senior_surcharge_start_age}
                  </p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'geo' && (
            <div className="card">
              <div className="card-header">
                <h2 className="font-semibold text-slate-900">Geographic Factors</h2>
              </div>
              <div className="card-body">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Region</th>
                      <th>Factor</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(config?.geographic_factors?.regions || {}).map(([region, factor]) => (
                      <tr key={region}>
                        <td className="capitalize">{region}</td>
                        <td>{factor}x</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === 'calc' && (
            <div className="card">
              <div className="card-header">
                <h2 className="font-semibold text-slate-900 flex items-center">
                  <Calculator className="w-5 h-5 mr-2" />
                  Premium Calculator
                </h2>
              </div>
              <div className="card-body space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="label">Species</label>
                    <select
                      className="select"
                      value={calcParams.species}
                      onChange={(e) => setCalcParams((p) => ({ ...p, species: e.target.value }))}
                    >
                      <option value="dog">Dog</option>
                      <option value="cat">Cat</option>
                      <option value="bird">Bird</option>
                      <option value="exotic">Exotic</option>
                    </select>
                  </div>
                  <div>
                    <label className="label">Breed</label>
                    <input
                      type="text"
                      className="input"
                      value={calcParams.breed}
                      onChange={(e) => setCalcParams((p) => ({ ...p, breed: e.target.value }))}
                    />
                  </div>
                  <div>
                    <label className="label">Age (Years)</label>
                    <input
                      type="number"
                      className="input"
                      min="0"
                      max="20"
                      value={calcParams.age_years}
                      onChange={(e) => setCalcParams((p) => ({ ...p, age_years: parseInt(e.target.value) }))}
                    />
                  </div>
                  <div>
                    <label className="label">Region</label>
                    <select
                      className="select"
                      value={calcParams.region}
                      onChange={(e) => setCalcParams((p) => ({ ...p, region: e.target.value }))}
                    >
                      <option value="northeast">Northeast</option>
                      <option value="southeast">Southeast</option>
                      <option value="midwest">Midwest</option>
                      <option value="southwest">Southwest</option>
                      <option value="west">West</option>
                    </select>
                  </div>
                  <div>
                    <label className="label">Deductible</label>
                    <select
                      className="select"
                      value={calcParams.deductible}
                      onChange={(e) => setCalcParams((p) => ({ ...p, deductible: parseInt(e.target.value) }))}
                    >
                      <option value={100}>$100</option>
                      <option value={250}>$250</option>
                      <option value={500}>$500</option>
                      <option value={750}>$750</option>
                      <option value={1000}>$1000</option>
                    </select>
                  </div>
                  <div>
                    <label className="label">Reimbursement</label>
                    <select
                      className="select"
                      value={calcParams.reimbursement_percent}
                      onChange={(e) => setCalcParams((p) => ({ ...p, reimbursement_percent: parseInt(e.target.value) }))}
                    >
                      <option value={70}>70%</option>
                      <option value={80}>80%</option>
                      <option value={90}>90%</option>
                    </select>
                  </div>
                </div>

                <button onClick={handleCalculate} className="btn-primary w-full">
                  Calculate Premium
                </button>

                {calcResult && (
                  <div className="mt-6 p-4 bg-primary-50 rounded-lg border border-primary-200">
                    <h3 className="font-semibold text-lg mb-4">Premium Breakdown</h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span>Base Rate:</span>
                        <span>{formatCurrency(calcResult.base_rate)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Breed Factor:</span>
                        <span>{calcResult.breed_factor}x</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Age Factor:</span>
                        <span>{calcResult.age_factor}x</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Geographic Factor:</span>
                        <span>{calcResult.geographic_factor}x</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Deductible Adjustment:</span>
                        <span>{calcResult.deductible_adjustment}x</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Reimbursement Adjustment:</span>
                        <span>{calcResult.reimbursement_adjustment}x</span>
                      </div>
                      <div className="border-t border-primary-200 pt-2 mt-2">
                        <div className="flex justify-between font-semibold text-lg">
                          <span>Monthly Premium:</span>
                          <span className="text-primary-600">{formatCurrency(calcResult.monthly_premium)}</span>
                        </div>
                        <div className="flex justify-between text-slate-600">
                          <span>Annual Premium:</span>
                          <span>{formatCurrency(calcResult.annual_premium)}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <div className="card">
            <div className="card-header">
              <h2 className="font-semibold text-slate-900">Configuration Version</h2>
            </div>
            <div className="card-body">
              <p className="text-2xl font-bold text-primary-600">{config?.version}</p>
              <p className="text-sm text-slate-500 mt-1">
                Last updated: {config?.updated_at ? new Date(config.updated_at).toLocaleDateString() : 'N/A'}
              </p>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <h2 className="font-semibold text-slate-900">Discounts</h2>
            </div>
            <div className="card-body space-y-2 text-sm">
              <div className="flex justify-between">
                <span>Multi-Pet:</span>
                <span className="font-medium">{((config?.discounts?.multi_pet || 0) * 100)}%</span>
              </div>
              <div className="flex justify-between">
                <span>Annual Payment:</span>
                <span className="font-medium">{((config?.discounts?.annual_payment || 0) * 100)}%</span>
              </div>
              <div className="flex justify-between">
                <span>Loyalty (per year):</span>
                <span className="font-medium">{((config?.discounts?.loyalty_per_year || 0) * 100)}%</span>
              </div>
              <div className="flex justify-between">
                <span>Max Loyalty:</span>
                <span className="font-medium">{((config?.discounts?.max_loyalty_discount || 0) * 100)}%</span>
              </div>
            </div>
          </div>

          {hasChanges && (
            <div className="card border-warning-200 bg-warning-50">
              <div className="card-header border-warning-200">
                <h2 className="font-semibold text-slate-900 flex items-center">
                  <AlertCircle className="w-4 h-4 mr-2 text-warning-600" />
                  Unsaved Changes
                </h2>
              </div>
              <div className="card-body space-y-4">
                <div>
                  <label className="label">Change Reason *</label>
                  <textarea
                    className="input"
                    rows={3}
                    placeholder="Describe why you're making this change..."
                    value={changeReason}
                    onChange={(e) => setChangeReason(e.target.value)}
                  />
                </div>
                <button
                  onClick={handleSubmit}
                  disabled={updateMutation.isPending}
                  className="btn-primary w-full flex items-center justify-center"
                >
                  <Save className="w-4 h-4 mr-2" />
                  {updateMutation.isPending ? 'Submitting...' : 'Submit for Approval'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
