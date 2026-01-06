import { useState, useRef } from 'react'
import {
  Search, Upload, X, Heart, Shield, DollarSign,
  Sparkles, ChevronRight, Camera, RefreshCw, Loader2,
  Dog, Cat
} from 'lucide-react'
import api from '../services/api'

// Sample pet images with categories
const SAMPLE_PETS = [
  {
    id: 1,
    name: 'Golden Retriever',
    species: 'Dog',
    breed: 'Golden Retriever',
    image: 'https://images.unsplash.com/photo-1552053831-71594a27632d?w=300&h=300&fit=crop',
    traits: ['Friendly', 'Active', 'Family-oriented']
  },
  {
    id: 2,
    name: 'German Shepherd',
    species: 'Dog',
    breed: 'German Shepherd',
    image: 'https://images.unsplash.com/photo-1589941013453-ec89f33b5e95?w=300&h=300&fit=crop',
    traits: ['Loyal', 'Protective', 'Intelligent']
  },
  {
    id: 3,
    name: 'Labrador',
    species: 'Dog',
    breed: 'Labrador Retriever',
    image: 'https://images.unsplash.com/photo-1579213838058-824f2f024be6?w=300&h=300&fit=crop',
    traits: ['Playful', 'Gentle', 'Outgoing']
  },
  {
    id: 4,
    name: 'French Bulldog',
    species: 'Dog',
    breed: 'French Bulldog',
    image: 'https://images.unsplash.com/photo-1583511655857-d19b40a7a54e?w=300&h=300&fit=crop',
    traits: ['Adaptable', 'Playful', 'Smart']
  },
  {
    id: 5,
    name: 'Beagle',
    species: 'Dog',
    breed: 'Beagle',
    image: 'https://images.unsplash.com/photo-1505628346881-b72b27e84530?w=300&h=300&fit=crop',
    traits: ['Curious', 'Merry', 'Friendly']
  },
  {
    id: 6,
    name: 'Persian Cat',
    species: 'Cat',
    breed: 'Persian',
    image: 'https://images.unsplash.com/photo-1574158622682-e40e69881006?w=300&h=300&fit=crop',
    traits: ['Calm', 'Affectionate', 'Quiet']
  },
  {
    id: 7,
    name: 'Maine Coon',
    species: 'Cat',
    breed: 'Maine Coon',
    image: 'https://images.unsplash.com/photo-1615497001839-b0a0eac3274c?w=300&h=300&fit=crop',
    traits: ['Gentle Giant', 'Playful', 'Social']
  },
  {
    id: 8,
    name: 'Siamese Cat',
    species: 'Cat',
    breed: 'Siamese',
    image: 'https://images.unsplash.com/photo-1513360371669-4adf3dd7dff8?w=300&h=300&fit=crop',
    traits: ['Vocal', 'Affectionate', 'Social']
  },
  {
    id: 9,
    name: 'British Shorthair',
    species: 'Cat',
    breed: 'British Shorthair',
    image: 'https://images.unsplash.com/photo-1596854407944-bf87f6fdd49e?w=300&h=300&fit=crop',
    traits: ['Easy-going', 'Loyal', 'Independent']
  },
  {
    id: 10,
    name: 'Bengal Cat',
    species: 'Cat',
    breed: 'Bengal',
    image: 'https://images.unsplash.com/photo-1606567595334-d39972c85dfd?w=300&h=300&fit=crop',
    traits: ['Energetic', 'Intelligent', 'Athletic']
  },
  {
    id: 11,
    name: 'Poodle',
    species: 'Dog',
    breed: 'Poodle',
    image: 'https://images.unsplash.com/photo-1616149255306-5c3e2e1a9842?w=300&h=300&fit=crop',
    traits: ['Intelligent', 'Active', 'Hypoallergenic']
  },
  {
    id: 12,
    name: 'Husky',
    species: 'Dog',
    breed: 'Siberian Husky',
    image: 'https://images.unsplash.com/photo-1605568427561-40dd23c2acea?w=300&h=300&fit=crop',
    traits: ['Energetic', 'Outgoing', 'Mischievous']
  }
]

// Generate recommendations based on pet type
function generateRecommendations(pet) {
  const baseRecommendations = {
    insurance: {
      title: 'Recommended Insurance Plan',
      plans: []
    },
    health: {
      title: 'Health Tips',
      tips: []
    },
    care: {
      title: 'Care Requirements',
      items: []
    },
    costs: {
      title: 'Estimated Monthly Costs',
      items: []
    }
  }

  // Dog-specific recommendations
  if (pet.species === 'Dog') {
    baseRecommendations.insurance.plans = [
      { name: 'Premium Plan', price: '$79.99/mo', coverage: '$20,000', recommended: true, reason: 'Best for active breeds' },
      { name: 'Standard Plan', price: '$49.99/mo', coverage: '$10,000', recommended: false, reason: 'Good basic coverage' }
    ]
    baseRecommendations.health.tips = [
      'Regular exercise - at least 30-60 minutes daily',
      'Annual vet checkups and vaccinations',
      'Dental cleaning recommended every 6-12 months',
      'Watch for hip dysplasia in larger breeds',
      'Keep up with heartworm prevention'
    ]
    baseRecommendations.care.items = [
      { item: 'Grooming', frequency: 'Weekly brushing, bath monthly' },
      { item: 'Exercise', frequency: '30-60 min daily walks' },
      { item: 'Training', frequency: 'Ongoing socialization recommended' },
      { item: 'Vet visits', frequency: 'Annual checkup + vaccinations' }
    ]
    baseRecommendations.costs.items = [
      { item: 'Food', cost: '$50-100' },
      { item: 'Treats & Toys', cost: '$20-40' },
      { item: 'Grooming', cost: '$30-80' },
      { item: 'Vet (averaged)', cost: '$50-100' },
      { item: 'Insurance', cost: '$30-80' }
    ]
  } else {
    // Cat-specific recommendations
    baseRecommendations.insurance.plans = [
      { name: 'Standard Plan', price: '$49.99/mo', coverage: '$10,000', recommended: true, reason: 'Perfect for indoor cats' },
      { name: 'Basic Plan', price: '$29.99/mo', coverage: '$5,000', recommended: false, reason: 'Essential coverage' }
    ]
    baseRecommendations.health.tips = [
      'Keep indoors for safety and longer lifespan',
      'Annual vet checkups and vaccinations',
      'Dental care - watch for gum disease',
      'Monitor weight - obesity is common in cats',
      'Provide scratching posts for claw health'
    ]
    baseRecommendations.care.items = [
      { item: 'Grooming', frequency: 'Brush 2-3 times weekly' },
      { item: 'Litter box', frequency: 'Clean daily, full change weekly' },
      { item: 'Play time', frequency: '15-30 min interactive play daily' },
      { item: 'Vet visits', frequency: 'Annual checkup + vaccinations' }
    ]
    baseRecommendations.costs.items = [
      { item: 'Food', cost: '$30-60' },
      { item: 'Litter', cost: '$15-30' },
      { item: 'Treats & Toys', cost: '$10-25' },
      { item: 'Vet (averaged)', cost: '$40-80' },
      { item: 'Insurance', cost: '$20-50' }
    ]
  }

  // Add breed-specific info
  baseRecommendations.breedInfo = {
    breed: pet.breed,
    species: pet.species,
    traits: pet.traits || ['Friendly', 'Loyal', 'Playful'],
    lifespan: pet.species === 'Dog' ? '10-15 years' : '12-18 years',
    size: pet.species === 'Dog' ? 'Medium to Large' : 'Small to Medium'
  }

  return baseRecommendations
}

export default function PetSelectPage() {
  const [filter, setFilter] = useState('all') // 'all', 'dog', 'cat'
  const [selectedPet, setSelectedPet] = useState(null)
  const [recommendations, setRecommendations] = useState(null)
  const [uploadedImage, setUploadedImage] = useState(null)
  const [uploadedPetInfo, setUploadedPetInfo] = useState(null)
  const [loading, setLoading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const fileInputRef = useRef(null)

  const filteredPets = SAMPLE_PETS.filter(pet => {
    if (filter === 'all') return true
    return pet.species.toLowerCase() === filter
  })

  const handlePetSelect = (pet) => {
    setSelectedPet(pet)
    setUploadedImage(null)
    setUploadedPetInfo(null)
    setLoading(true)

    // Simulate API call for recommendations
    setTimeout(() => {
      const recs = generateRecommendations(pet)
      setRecommendations(recs)
      setLoading(false)
    }, 800)
  }

  const handleImageUpload = (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Validate file type
    if (!file.type.startsWith('image/')) {
      alert('Please upload an image file')
      return
    }

    // Create preview
    const reader = new FileReader()
    reader.onload = (event) => {
      setUploadedImage(event.target?.result)
      setSelectedPet(null)
      setRecommendations(null)
      analyzeUploadedImage(file)
    }
    reader.readAsDataURL(file)
  }

  const analyzeUploadedImage = async (file) => {
    setAnalyzing(true)

    // Simulate image analysis (in production, this would call an AI service)
    setTimeout(() => {
      // Mock detection - randomly assign dog or cat
      const detectedSpecies = Math.random() > 0.5 ? 'Dog' : 'Cat'
      const mockBreeds = detectedSpecies === 'Dog'
        ? ['Mixed Breed', 'Labrador Mix', 'Terrier Mix', 'Shepherd Mix']
        : ['Domestic Shorthair', 'Tabby', 'Mixed Breed', 'Domestic Longhair']

      const detectedPet = {
        id: 'uploaded',
        name: 'Your Pet',
        species: detectedSpecies,
        breed: mockBreeds[Math.floor(Math.random() * mockBreeds.length)],
        traits: detectedSpecies === 'Dog'
          ? ['Loyal', 'Friendly', 'Active']
          : ['Independent', 'Curious', 'Affectionate'],
        confidence: Math.floor(Math.random() * 20) + 80 // 80-99%
      }

      setUploadedPetInfo(detectedPet)
      const recs = generateRecommendations(detectedPet)
      setRecommendations(recs)
      setAnalyzing(false)
    }, 1500)
  }

  const clearSelection = () => {
    setSelectedPet(null)
    setUploadedImage(null)
    setUploadedPetInfo(null)
    setRecommendations(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <section className="text-center">
        <div className="inline-flex items-center justify-center h-16 w-16 rounded-full bg-gradient-to-r from-pet-orange to-primary-600 text-white mb-4">
          <Sparkles className="h-8 w-8" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Pet Recommendations</h1>
        <p className="text-gray-600 max-w-2xl mx-auto">
          Select a pet type or upload a photo of your pet to get personalized insurance recommendations,
          health tips, and care guidelines - completely free!
        </p>
      </section>

      {/* Upload Section */}
      <section className="card bg-gradient-to-r from-primary-50 to-pet-orange/10 border-2 border-dashed border-primary-300">
        <div className="text-center py-4">
          <input
            type="file"
            accept="image/*"
            onChange={handleImageUpload}
            ref={fileInputRef}
            className="hidden"
            id="pet-upload"
          />

          {uploadedImage ? (
            <div className="space-y-4">
              <div className="relative inline-block">
                <img
                  src={uploadedImage}
                  alt="Uploaded pet"
                  className="h-48 w-48 object-cover rounded-xl shadow-lg mx-auto"
                />
                <button
                  onClick={clearSelection}
                  className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 hover:bg-red-600"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
              {analyzing ? (
                <div className="flex items-center justify-center space-x-2 text-primary-600">
                  <Loader2 className="h-5 w-5 animate-spin" />
                  <span>Analyzing your pet...</span>
                </div>
              ) : uploadedPetInfo && (
                <div className="bg-white rounded-lg p-4 max-w-sm mx-auto shadow">
                  <p className="font-semibold text-lg">{uploadedPetInfo.species} Detected!</p>
                  <p className="text-gray-600">Breed: {uploadedPetInfo.breed}</p>
                  <p className="text-sm text-green-600">Confidence: {uploadedPetInfo.confidence}%</p>
                </div>
              )}
            </div>
          ) : (
            <label
              htmlFor="pet-upload"
              className="cursor-pointer block"
            >
              <div className="inline-flex items-center justify-center h-20 w-20 rounded-full bg-white shadow-md mb-4">
                <Camera className="h-10 w-10 text-primary-600" />
              </div>
              <p className="text-lg font-semibold text-gray-900">Upload Your Pet's Photo</p>
              <p className="text-gray-500 text-sm mt-1">
                We'll analyze the image and provide personalized recommendations
              </p>
              <button className="mt-4 btn-primary inline-flex items-center space-x-2">
                <Upload className="h-4 w-4" />
                <span>Choose Image</span>
              </button>
            </label>
          )}
        </div>
      </section>

      {/* Filter Tabs */}
      <section>
        <div className="flex items-center justify-center space-x-2 mb-6">
          <button
            onClick={() => setFilter('all')}
            className={`px-6 py-2 rounded-full font-medium transition-colors ${
              filter === 'all'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            All Pets
          </button>
          <button
            onClick={() => setFilter('dog')}
            className={`px-6 py-2 rounded-full font-medium transition-colors inline-flex items-center space-x-2 ${
              filter === 'dog'
                ? 'bg-pet-orange text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            <Dog className="h-4 w-4" />
            <span>Dogs</span>
          </button>
          <button
            onClick={() => setFilter('cat')}
            className={`px-6 py-2 rounded-full font-medium transition-colors inline-flex items-center space-x-2 ${
              filter === 'cat'
                ? 'bg-purple-600 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            <Cat className="h-4 w-4" />
            <span>Cats</span>
          </button>
        </div>

        {/* Pet Grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
          {filteredPets.map(pet => (
            <button
              key={pet.id}
              onClick={() => handlePetSelect(pet)}
              className={`group relative rounded-xl overflow-hidden shadow-md hover:shadow-xl transition-all transform hover:-translate-y-1 ${
                selectedPet?.id === pet.id ? 'ring-4 ring-primary-500' : ''
              }`}
            >
              <img
                src={pet.image}
                alt={pet.name}
                className="w-full h-40 object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent" />
              <div className="absolute bottom-0 left-0 right-0 p-3 text-white">
                <p className="font-semibold text-sm">{pet.name}</p>
                <p className="text-xs text-white/80">{pet.breed}</p>
              </div>
              <div className={`absolute top-2 right-2 h-6 w-6 rounded-full flex items-center justify-center ${
                pet.species === 'Dog' ? 'bg-pet-orange' : 'bg-purple-600'
              }`}>
                {pet.species === 'Dog' ? (
                  <Dog className="h-3 w-3 text-white" />
                ) : (
                  <Cat className="h-3 w-3 text-white" />
                )}
              </div>
              {selectedPet?.id === pet.id && (
                <div className="absolute top-2 left-2 bg-green-500 text-white text-xs px-2 py-1 rounded-full">
                  Selected
                </div>
              )}
            </button>
          ))}
        </div>
      </section>

      {/* Recommendations Section */}
      {(selectedPet || uploadedPetInfo) && (
        <section className="space-y-6 animate-fade-in">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900 flex items-center">
              <Sparkles className="h-6 w-6 text-pet-orange mr-2" />
              Recommendations for {selectedPet?.name || uploadedPetInfo?.breed}
            </h2>
            <button
              onClick={clearSelection}
              className="text-gray-500 hover:text-gray-700 flex items-center space-x-1"
            >
              <RefreshCw className="h-4 w-4" />
              <span>Start Over</span>
            </button>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
              <span className="ml-3 text-gray-600">Generating recommendations...</span>
            </div>
          ) : recommendations && (
            <div className="grid md:grid-cols-2 gap-6">
              {/* Breed Info Card */}
              <div className="card bg-gradient-to-br from-primary-50 to-white">
                <h3 className="text-lg font-bold mb-4 flex items-center">
                  <Heart className="h-5 w-5 text-red-500 mr-2" />
                  About {recommendations.breedInfo.breed}
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Species</span>
                    <span className="font-medium">{recommendations.breedInfo.species}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Typical Lifespan</span>
                    <span className="font-medium">{recommendations.breedInfo.lifespan}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Size</span>
                    <span className="font-medium">{recommendations.breedInfo.size}</span>
                  </div>
                  <div>
                    <span className="text-gray-600 block mb-2">Traits</span>
                    <div className="flex flex-wrap gap-2">
                      {recommendations.breedInfo.traits.map(trait => (
                        <span key={trait} className="px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-sm">
                          {trait}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Insurance Recommendations */}
              <div className="card">
                <h3 className="text-lg font-bold mb-4 flex items-center">
                  <Shield className="h-5 w-5 text-primary-600 mr-2" />
                  {recommendations.insurance.title}
                </h3>
                <div className="space-y-3">
                  {recommendations.insurance.plans.map(plan => (
                    <div
                      key={plan.name}
                      className={`p-4 rounded-lg border-2 ${
                        plan.recommended
                          ? 'border-primary-500 bg-primary-50'
                          : 'border-gray-200'
                      }`}
                    >
                      {plan.recommended && (
                        <span className="text-xs font-semibold text-primary-600 uppercase">
                          Recommended
                        </span>
                      )}
                      <div className="flex justify-between items-center mt-1">
                        <span className="font-bold text-lg">{plan.name}</span>
                        <span className="text-primary-600 font-bold">{plan.price}</span>
                      </div>
                      <p className="text-sm text-gray-600">Coverage up to {plan.coverage}</p>
                      <p className="text-xs text-gray-500 mt-1">{plan.reason}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Health Tips */}
              <div className="card">
                <h3 className="text-lg font-bold mb-4 flex items-center">
                  <Heart className="h-5 w-5 text-red-500 mr-2" />
                  {recommendations.health.title}
                </h3>
                <ul className="space-y-2">
                  {recommendations.health.tips.map((tip, i) => (
                    <li key={i} className="flex items-start space-x-2">
                      <ChevronRight className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                      <span className="text-gray-700">{tip}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Care Requirements */}
              <div className="card">
                <h3 className="text-lg font-bold mb-4 flex items-center">
                  <Search className="h-5 w-5 text-blue-500 mr-2" />
                  {recommendations.care.title}
                </h3>
                <div className="space-y-3">
                  {recommendations.care.items.map(item => (
                    <div key={item.item} className="flex justify-between py-2 border-b border-gray-100 last:border-0">
                      <span className="font-medium text-gray-700">{item.item}</span>
                      <span className="text-gray-600 text-sm">{item.frequency}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Monthly Costs */}
              <div className="card md:col-span-2">
                <h3 className="text-lg font-bold mb-4 flex items-center">
                  <DollarSign className="h-5 w-5 text-green-600 mr-2" />
                  {recommendations.costs.title}
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  {recommendations.costs.items.map(item => (
                    <div key={item.item} className="text-center p-4 bg-gray-50 rounded-lg">
                      <p className="text-sm text-gray-600">{item.item}</p>
                      <p className="text-lg font-bold text-gray-900">{item.cost}</p>
                    </div>
                  ))}
                </div>
                <div className="mt-4 p-4 bg-primary-50 rounded-lg text-center">
                  <p className="text-sm text-gray-600">Estimated Total Monthly Cost</p>
                  <p className="text-2xl font-bold text-primary-600">
                    ${recommendations.costs.items.reduce((sum, item) => {
                      const avg = item.cost.replace('$', '').split('-').map(Number)
                      return sum + (avg.length === 2 ? (avg[0] + avg[1]) / 2 : avg[0])
                    }, 0).toFixed(0)} - ${recommendations.costs.items.reduce((sum, item) => {
                      const avg = item.cost.replace('$', '').split('-').map(Number)
                      return sum + (avg.length === 2 ? avg[1] : avg[0])
                    }, 0).toFixed(0)}
                  </p>
                </div>
              </div>
            </div>
          )}
        </section>
      )}

      {/* CTA Section */}
      {!selectedPet && !uploadedPetInfo && (
        <section className="card bg-gradient-to-r from-primary-600 to-primary-700 text-white text-center">
          <h3 className="text-xl font-bold mb-2">Ready to Protect Your Pet?</h3>
          <p className="text-primary-100 mb-4">
            Get comprehensive insurance coverage starting at just $29.99/month
          </p>
          <a
            href="/register"
            className="inline-flex items-center space-x-2 bg-white text-primary-700 px-6 py-3 rounded-lg font-semibold hover:bg-primary-50 transition-colors"
          >
            <span>Get Started Free</span>
            <ChevronRight className="h-5 w-5" />
          </a>
        </section>
      )}
    </div>
  )
}
