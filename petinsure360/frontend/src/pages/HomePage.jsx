import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  User, PawPrint, FileText, AlertCircle, ArrowRight, Shield, Heart, Clock,
  DollarSign, TrendingUp, CheckCircle, XCircle, Loader2, LogIn
} from 'lucide-react'
import api from '../services/api'

// Guest homepage (not logged in)
function GuestHomePage() {
  const features = [
    {
      icon: Shield,
      title: 'Comprehensive Coverage',
      description: 'Protection for accidents, illnesses, wellness, and more'
    },
    {
      icon: Heart,
      title: 'All Pets Welcome',
      description: 'Coverage for dogs and cats of all breeds and ages'
    },
    {
      icon: Clock,
      title: 'Fast Claims Processing',
      description: 'Average claim processing time of 3-5 business days'
    }
  ]

  const steps = [
    { icon: User, title: 'Register', description: 'Create your account', path: '/register' },
    { icon: PawPrint, title: 'Add Pet', description: 'Add your furry friend', path: '/add-pet' },
    { icon: FileText, title: 'Buy Policy', description: 'Choose your coverage', path: '/policy' },
    { icon: AlertCircle, title: 'Submit Claim', description: 'File a claim when needed', path: '/claim' },
  ]

  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <section className="text-center py-12 bg-gradient-to-r from-primary-600 to-primary-700 rounded-2xl text-white">
        <div className="max-w-3xl mx-auto px-4">
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            Protect Your Best Friend
          </h1>
          <p className="text-xl text-primary-100 mb-8">
            Comprehensive pet insurance coverage for dogs and cats.
            Because they're family too.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              to="/register"
              className="inline-flex items-center space-x-2 bg-white text-primary-700 px-6 py-3 rounded-lg font-semibold hover:bg-primary-50 transition-colors"
            >
              <span>Get Started</span>
              <ArrowRight className="h-5 w-5" />
            </Link>
            <Link
              to="/login"
              className="inline-flex items-center space-x-2 bg-primary-500 text-white px-6 py-3 rounded-lg font-semibold hover:bg-primary-400 transition-colors border border-primary-400"
            >
              <LogIn className="h-5 w-5" />
              <span>Sign In</span>
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="grid md:grid-cols-3 gap-6">
        {features.map(({ icon: Icon, title, description }) => (
          <div key={title} className="card text-center">
            <div className="inline-flex items-center justify-center h-12 w-12 rounded-full bg-primary-100 text-primary-600 mb-4">
              <Icon className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-semibold mb-2">{title}</h3>
            <p className="text-gray-600">{description}</p>
          </div>
        ))}
      </section>

      {/* How It Works */}
      <section>
        <h2 className="text-2xl font-bold text-center mb-8">How It Works</h2>
        <div className="grid md:grid-cols-4 gap-6">
          {steps.map(({ icon: Icon, title, description, path }, index) => (
            <Link
              key={title}
              to={path}
              className="card hover:shadow-lg transition-shadow group"
            >
              <div className="flex items-center justify-between mb-4">
                <span className="text-3xl font-bold text-gray-200">{index + 1}</span>
                <div className="h-10 w-10 rounded-full bg-pet-orange/10 text-pet-orange flex items-center justify-center group-hover:bg-pet-orange group-hover:text-white transition-colors">
                  <Icon className="h-5 w-5" />
                </div>
              </div>
              <h3 className="text-lg font-semibold mb-1">{title}</h3>
              <p className="text-gray-600 text-sm">{description}</p>
            </Link>
          ))}
        </div>
      </section>

      {/* Plans Preview */}
      <section className="card">
        <h2 className="text-2xl font-bold mb-6 text-center">Our Plans</h2>
        <div className="grid md:grid-cols-4 gap-4">
          {[
            { name: 'Basic', price: '$29.99', coverage: '$5,000', color: 'gray' },
            { name: 'Standard', price: '$49.99', coverage: '$10,000', color: 'blue' },
            { name: 'Premium', price: '$79.99', coverage: '$20,000', color: 'purple', popular: true },
            { name: 'Unlimited', price: '$99.99', coverage: 'Unlimited', color: 'orange' },
          ].map(plan => (
            <div
              key={plan.name}
              className={`p-4 rounded-lg border-2 ${
                plan.popular ? 'border-pet-orange bg-pet-orange/5' : 'border-gray-200'
              }`}
            >
              {plan.popular && (
                <span className="text-xs font-semibold text-pet-orange uppercase">Most Popular</span>
              )}
              <h3 className="text-lg font-bold mt-1">{plan.name}</h3>
              <p className="text-2xl font-bold text-primary-600 my-2">{plan.price}<span className="text-sm text-gray-500">/mo</span></p>
              <p className="text-sm text-gray-600">Up to {plan.coverage} coverage</p>
            </div>
          ))}
        </div>
        <div className="text-center mt-6">
          <Link to="/policy" className="btn-primary inline-flex items-center space-x-2">
            <span>View All Plans</span>
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>

      {/* Data Platform Info */}
      <section className="bg-gray-800 rounded-2xl p-8 text-white">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-2xl font-bold mb-4">Powered by Azure Data Platform</h2>
          <p className="text-gray-300 mb-6">
            This demo showcases a complete enterprise data platform built on Azure Databricks,
            Synapse, and Data Lake Gen2 with a medallion lakehouse architecture.
          </p>
          <div className="flex flex-wrap justify-center gap-4 text-sm">
            <span className="px-3 py-1 bg-gray-700 rounded-full">Azure Databricks</span>
            <span className="px-3 py-1 bg-gray-700 rounded-full">Azure Synapse</span>
            <span className="px-3 py-1 bg-gray-700 rounded-full">ADLS Gen2</span>
            <span className="px-3 py-1 bg-gray-700 rounded-full">Delta Lake</span>
            <span className="px-3 py-1 bg-gray-700 rounded-full">FastAPI</span>
            <span className="px-3 py-1 bg-gray-700 rounded-full">React</span>
          </div>
        </div>
      </section>
    </div>
  )
}

// User Dashboard (logged in)
function UserDashboard({ user }) {
  const [pets, setPets] = useState([])
  const [policies, setPolicies] = useState([])
  const [claims, setClaims] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const [petsRes, policiesRes, claimsRes] = await Promise.all([
          api.get(`/pets/customer/${user.customer_id}`),
          api.get(`/policies/customer/${user.customer_id}`),
          api.get(`/claims/customer/${user.customer_id}`)
        ])

        setPets(petsRes.data.pets || [])
        setPolicies(policiesRes.data.policies || [])
        setClaims(claimsRes.data.claims || [])
      } catch (err) {
        console.error('Error fetching user data:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchUserData()
  }, [user.customer_id])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
        <span className="ml-3 text-gray-600">Loading your dashboard...</span>
      </div>
    )
  }

  const totalPremium = policies.reduce((sum, p) => sum + (p.monthly_premium || 0), 0)
  const activePolicies = policies.filter(p => p.status === 'Active').length
  const pendingClaims = claims.filter(c => !['Approved', 'Denied', 'Paid'].includes(c.status)).length
  const totalClaimAmount = claims.reduce((sum, c) => sum + (c.claim_amount || 0), 0)

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <section className="bg-gradient-to-r from-primary-600 to-primary-700 rounded-2xl p-8 text-white">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">
              Welcome back, {user.full_name || `${user.first_name} ${user.last_name}`}!
            </h1>
            <p className="text-primary-100">
              Customer since {user.customer_since || 'Today'} | {user.email}
            </p>
          </div>
          <div className="mt-4 md:mt-0">
            <span className={`px-4 py-2 rounded-full text-sm font-semibold ${
              user.customer_value_tier === 'Platinum' ? 'bg-purple-500' :
              user.customer_value_tier === 'Gold' ? 'bg-yellow-500' :
              user.customer_value_tier === 'Silver' ? 'bg-gray-400' :
              'bg-orange-500'
            }`}>
              {user.customer_value_tier || 'New'} Member
            </span>
          </div>
        </div>
      </section>

      {/* Quick Stats */}
      <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card text-center">
          <PawPrint className="h-8 w-8 text-pet-orange mx-auto mb-2" />
          <p className="text-3xl font-bold text-gray-900">{pets.length}</p>
          <p className="text-gray-600 text-sm">Pets</p>
        </div>
        <div className="card text-center">
          <FileText className="h-8 w-8 text-primary-600 mx-auto mb-2" />
          <p className="text-3xl font-bold text-gray-900">{activePolicies}</p>
          <p className="text-gray-600 text-sm">Active Policies</p>
        </div>
        <div className="card text-center">
          <DollarSign className="h-8 w-8 text-green-600 mx-auto mb-2" />
          <p className="text-3xl font-bold text-gray-900">${totalPremium.toFixed(2)}</p>
          <p className="text-gray-600 text-sm">Monthly Premium</p>
        </div>
        <div className="card text-center">
          <AlertCircle className="h-8 w-8 text-blue-600 mx-auto mb-2" />
          <p className="text-3xl font-bold text-gray-900">{claims.length}</p>
          <p className="text-gray-600 text-sm">Total Claims</p>
        </div>
      </section>

      {/* My Pets */}
      <section className="card">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold flex items-center">
            <PawPrint className="h-6 w-6 text-pet-orange mr-2" />
            My Pets
          </h2>
          <Link to="/add-pet" className="btn-secondary text-sm">
            + Add Pet
          </Link>
        </div>

        {pets.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <PawPrint className="h-12 w-12 mx-auto mb-3 opacity-30" />
            <p>No pets registered yet</p>
            <Link to="/add-pet" className="text-primary-600 hover:underline">Add your first pet</Link>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {pets.map(pet => (
              <div key={pet.pet_id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex items-center space-x-3">
                  <div className={`h-12 w-12 rounded-full flex items-center justify-center ${
                    pet.species === 'Dog' ? 'bg-orange-100 text-orange-600' : 'bg-purple-100 text-purple-600'
                  }`}>
                    <PawPrint className="h-6 w-6" />
                  </div>
                  <div>
                    <h3 className="font-semibold">{pet.pet_name}</h3>
                    <p className="text-sm text-gray-500">{pet.species} - {pet.breed}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* My Policies */}
      <section className="card">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold flex items-center">
            <FileText className="h-6 w-6 text-primary-600 mr-2" />
            My Policies
          </h2>
          <Link to="/policy" className="btn-secondary text-sm">
            + Buy Policy
          </Link>
        </div>

        {policies.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <FileText className="h-12 w-12 mx-auto mb-3 opacity-30" />
            <p>No policies yet</p>
            <Link to="/policy" className="text-primary-600 hover:underline">Get a quote</Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Policy #</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Plan</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Premium</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Coverage</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {policies.slice(0, 5).map(policy => (
                  <tr key={policy.policy_id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium">{policy.policy_number || policy.policy_id}</td>
                    <td className="px-4 py-3 text-sm">{policy.plan_type || policy.plan_name}</td>
                    <td className="px-4 py-3 text-sm">${policy.monthly_premium}/mo</td>
                    <td className="px-4 py-3 text-sm">${policy.coverage_limit || policy.annual_limit}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        policy.status === 'Active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                      }`}>
                        {policy.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Recent Claims */}
      <section className="card">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold flex items-center">
            <AlertCircle className="h-6 w-6 text-blue-600 mr-2" />
            Recent Claims
          </h2>
          <Link to="/claim" className="btn-secondary text-sm">
            + Submit Claim
          </Link>
        </div>

        {claims.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <AlertCircle className="h-12 w-12 mx-auto mb-3 opacity-30" />
            <p>No claims submitted yet</p>
            <Link to="/claim" className="text-primary-600 hover:underline">File a claim</Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Claim #</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {claims.slice(0, 5).map(claim => (
                  <tr key={claim.claim_id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm font-medium">{claim.claim_number || claim.claim_id}</td>
                    <td className="px-4 py-3 text-sm">{claim.service_date || claim.submitted_date}</td>
                    <td className="px-4 py-3 text-sm">{claim.claim_type}</td>
                    <td className="px-4 py-3 text-sm">${claim.claim_amount?.toFixed(2)}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center px-2 py-1 text-xs rounded-full ${
                        claim.status === 'Approved' || claim.status === 'Paid' ? 'bg-green-100 text-green-800' :
                        claim.status === 'Denied' ? 'bg-red-100 text-red-800' :
                        claim.status === 'Under Review' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-blue-100 text-blue-800'
                      }`}>
                        {claim.status === 'Approved' || claim.status === 'Paid' ? (
                          <CheckCircle className="h-3 w-3 mr-1" />
                        ) : claim.status === 'Denied' ? (
                          <XCircle className="h-3 w-3 mr-1" />
                        ) : null}
                        {claim.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Quick Actions */}
      <section className="grid md:grid-cols-3 gap-4">
        <Link to="/add-pet" className="card hover:shadow-lg transition-shadow group text-center">
          <PawPrint className="h-8 w-8 text-pet-orange mx-auto mb-2 group-hover:scale-110 transition-transform" />
          <h3 className="font-semibold">Add New Pet</h3>
          <p className="text-sm text-gray-500">Register another furry friend</p>
        </Link>
        <Link to="/policy" className="card hover:shadow-lg transition-shadow group text-center">
          <FileText className="h-8 w-8 text-primary-600 mx-auto mb-2 group-hover:scale-110 transition-transform" />
          <h3 className="font-semibold">Get New Policy</h3>
          <p className="text-sm text-gray-500">Protect another pet</p>
        </Link>
        <Link to="/claim" className="card hover:shadow-lg transition-shadow group text-center">
          <AlertCircle className="h-8 w-8 text-blue-600 mx-auto mb-2 group-hover:scale-110 transition-transform" />
          <h3 className="font-semibold">Submit Claim</h3>
          <p className="text-sm text-gray-500">File an insurance claim</p>
        </Link>
      </section>
    </div>
  )
}

// Main HomePage component
export default function HomePage({ user }) {
  if (user) {
    return <UserDashboard user={user} />
  }
  return <GuestHomePage />
}
