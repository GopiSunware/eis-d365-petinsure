import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { PawPrint, CheckCircle } from 'lucide-react'
import api from '../services/api'

export default function AddPetPage({ user }) {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(null)
  const [error, setError] = useState(null)

  const [formData, setFormData] = useState({
    customer_id: '',
    pet_name: '',
    species: 'Dog',
    breed: '',
    gender: 'Male',
    date_of_birth: '',
    weight_lbs: '',
    color: '',
    microchip_id: '',
    is_neutered: false,
    pre_existing_conditions: '',
    vaccination_status: 'Up-to-date'
  })

  useEffect(() => {
    // Use logged-in user's customer_id if available
    if (user?.customer_id) {
      setFormData(prev => ({ ...prev, customer_id: user.customer_id }))
    } else {
      const savedCustomerId = localStorage.getItem('customer_id')
      if (savedCustomerId) {
        setFormData(prev => ({ ...prev, customer_id: savedCustomerId }))
      }
    }
  }, [user])

  // Comprehensive breed lists for all species (matching QuotePage)
  const dogBreeds = ['Golden Retriever', 'Labrador Retriever', 'German Shepherd', 'Bulldog', 'Poodle', 'Beagle', 'Rottweiler', 'Yorkshire Terrier', 'Boxer', 'Dachshund', 'Other']
  const catBreeds = ['Persian', 'Maine Coon', 'Ragdoll', 'British Shorthair', 'Siamese', 'Bengal', 'Abyssinian', 'Sphynx', 'Scottish Fold', 'Domestic Shorthair', 'Other']
  const birdBreeds = ['Parakeet', 'Cockatiel', 'Parrot', 'Canary', 'Finch', 'Macaw', 'Cockatoo', 'Lovebird', 'Conure', 'Other']
  const rabbitBreeds = ['Holland Lop', 'Mini Rex', 'Netherland Dwarf', 'Lionhead', 'Flemish Giant', 'Angora', 'Dutch', 'Rex', 'Mixed Breed', 'Other']
  const reptileBreeds = ['Bearded Dragon', 'Leopard Gecko', 'Ball Python', 'Corn Snake', 'Iguana', 'Chameleon', 'Tortoise', 'Turtle', 'Other']

  // Get breeds based on selected species
  const getBreedList = (species) => {
    switch (species) {
      case 'Dog':
        return dogBreeds
      case 'Cat':
        return catBreeds
      case 'Bird':
        return birdBreeds
      case 'Rabbit':
        return rabbitBreeds
      case 'Reptile':
        return reptileBreeds
      default:
        return []
    }
  }

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    try {
      const submitData = {
        ...formData,
        weight_lbs: parseFloat(formData.weight_lbs)
      }
      const response = await api.post('/pets/', submitData)
      setSuccess(response.data)
      localStorage.setItem('pet_id', response.data.pet_id)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add pet. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  if (success) {
    return (
      <div className="max-w-md mx-auto">
        <div className="card text-center">
          <div className="inline-flex items-center justify-center h-16 w-16 rounded-full bg-green-100 text-green-600 mb-4">
            <CheckCircle className="h-8 w-8" />
          </div>
          <h2 className="text-2xl font-bold mb-2">Pet Added!</h2>
          <p className="text-gray-600 mb-4">
            {success.pet_name} has been registered successfully!
          </p>
          <p className="text-sm text-gray-500 mb-6">
            Pet ID: <span className="font-mono font-bold">{success.pet_id}</span>
          </p>
          <div className="space-y-3">
            <button
              onClick={() => navigate('/policy')}
              className="btn-primary w-full"
            >
              Buy Insurance Policy
            </button>
            <button
              onClick={() => {
                setSuccess(null)
                setFormData({
                  ...formData,
                  pet_name: '',
                  breed: '',
                  date_of_birth: '',
                  weight_lbs: '',
                  color: '',
                  microchip_id: '',
                  is_neutered: false,
                  pre_existing_conditions: ''
                })
              }}
              className="btn-secondary w-full"
            >
              Add Another Pet
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="card">
        <div className="flex items-center space-x-3 mb-6">
          <div className="h-10 w-10 rounded-full bg-pet-orange/10 text-pet-orange flex items-center justify-center">
            <PawPrint className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">Add Your Pet</h1>
            <p className="text-gray-600">Tell us about your furry friend</p>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Customer ID */}
          <div>
            <label className="label">Customer ID *</label>
            <input
              type="text"
              name="customer_id"
              value={formData.customer_id}
              onChange={handleChange}
              required
              className="input-field"
              placeholder="CUST-XXXXXXXX"
            />
            <p className="text-xs text-gray-500 mt-1">From registration or enter existing customer ID</p>
          </div>

          {/* Pet Name and Species */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Pet Name *</label>
              <input
                type="text"
                name="pet_name"
                value={formData.pet_name}
                onChange={handleChange}
                required
                className="input-field"
                placeholder="Buddy"
              />
            </div>
            <div>
              <label className="label">Species *</label>
              <select
                name="species"
                value={formData.species}
                onChange={handleChange}
                required
                className="input-field"
              >
                <option value="Dog">🐕 Dog</option>
                <option value="Cat">🐈 Cat</option>
                <option value="Bird">🦜 Bird</option>
                <option value="Rabbit">🐰 Rabbit</option>
                <option value="Reptile">🦎 Reptile</option>
              </select>
            </div>
          </div>

          {/* Breed and Gender */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Breed *</label>
              <select
                name="breed"
                value={formData.breed}
                onChange={handleChange}
                required
                className="input-field"
              >
                <option value="">Select breed...</option>
                {getBreedList(formData.species).map(breed => (
                  <option key={breed} value={breed}>{breed}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Gender *</label>
              <select
                name="gender"
                value={formData.gender}
                onChange={handleChange}
                required
                className="input-field"
              >
                <option value="Male">Male</option>
                <option value="Female">Female</option>
              </select>
            </div>
          </div>

          {/* DOB and Weight */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Date of Birth *</label>
              <input
                type="date"
                name="date_of_birth"
                value={formData.date_of_birth}
                onChange={handleChange}
                required
                className="input-field"
              />
            </div>
            <div>
              <label className="label">Weight (lbs) *</label>
              <input
                type="number"
                name="weight_lbs"
                value={formData.weight_lbs}
                onChange={handleChange}
                required
                min="1"
                max="300"
                step="0.1"
                className="input-field"
                placeholder="45"
              />
            </div>
          </div>

          {/* Color and Microchip */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Color/Markings</label>
              <input
                type="text"
                name="color"
                value={formData.color}
                onChange={handleChange}
                className="input-field"
                placeholder="Golden"
              />
            </div>
            <div>
              <label className="label">Microchip ID</label>
              <input
                type="text"
                name="microchip_id"
                value={formData.microchip_id}
                onChange={handleChange}
                className="input-field"
                placeholder="Optional"
              />
            </div>
          </div>

          {/* Vaccination Status */}
          <div>
            <label className="label">Vaccination Status</label>
            <select
              name="vaccination_status"
              value={formData.vaccination_status}
              onChange={handleChange}
              className="input-field"
            >
              <option value="Up-to-date">Up-to-date</option>
              <option value="Partial">Partial</option>
              <option value="Unknown">Unknown</option>
            </select>
          </div>

          {/* Pre-existing Conditions */}
          <div>
            <label className="label">Pre-existing Conditions</label>
            <textarea
              name="pre_existing_conditions"
              value={formData.pre_existing_conditions}
              onChange={handleChange}
              className="input-field"
              rows="2"
              placeholder="List any known health conditions (optional)"
            />
          </div>

          {/* Neutered */}
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              name="is_neutered"
              checked={formData.is_neutered}
              onChange={handleChange}
              className="h-4 w-4 text-primary-600 rounded"
            />
            <label className="text-sm text-gray-700">
              Pet is spayed/neutered
            </label>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full disabled:opacity-50"
          >
            {loading ? 'Adding Pet...' : 'Add Pet'}
          </button>
        </form>
      </div>
    </div>
  )
}
