/**
 * Build context object for AI chat
 * Includes current app state, customer data, and page-specific context
 */

// Page-specific detailed context for better AI responses
const PAGE_CONTEXT = {
  dashboard: {
    description: 'Customer dashboard overview',
    shows: [
      'Policy summary and status',
      'Pet information cards',
      'Recent claims history',
      'Quick action buttons'
    ],
    userIntent: [
      'Check policy status',
      'View pet coverage',
      'Submit new claims',
      'Track existing claims'
    ],
    tips: [
      'Click on a pet card for detailed coverage',
      'Use Submit Claim to start a new claim',
      'Check Claims History for past submissions'
    ]
  },
  claims: {
    description: 'Claims management page',
    shows: [
      'Claims list with status',
      'Processing timeline',
      'Reimbursement amounts',
      'Document uploads'
    ],
    userIntent: [
      'Check claim status',
      'Upload documents',
      'Track reimbursements',
      'Understand decisions'
    ],
    tips: [
      'Claims typically process within 5-7 business days',
      'Upload all required documents for faster processing',
      'Contact support for claims pending over 10 days'
    ]
  },
  policies: {
    description: 'Policy details page',
    shows: [
      'Coverage limits and deductibles',
      'Covered conditions',
      'Exclusions',
      'Premium information'
    ],
    userIntent: [
      'Understand coverage',
      'Check limits',
      'Review exclusions',
      'Update policy'
    ],
    tips: [
      'Annual limit resets on policy anniversary',
      'Pre-existing conditions are typically excluded',
      'Deductible applies per incident or per year depending on plan'
    ]
  },
  pets: {
    description: 'Pet profiles page',
    shows: [
      'Pet health records',
      'Vaccination status',
      'Medical history',
      'Coverage details per pet'
    ],
    userIntent: [
      'Update pet info',
      'Add medical records',
      'Check coverage per pet',
      'Add new pet'
    ],
    tips: [
      'Keep pet records up to date for faster claims',
      'Annual wellness exams may be covered',
      'Adding new pets may affect premium'
    ]
  }
};

export function buildChatContext(options = {}) {
  const { currentPage = 'dashboard', customerData, petData, claimData } = options;

  const context = {
    currentView: currentPage,
    timestamp: new Date().toISOString(),
    application: 'PetInsure360 Customer Portal'
  };

  // Add customer info if available
  if (customerData) {
    context.customer = {
      id: customerData.id,
      name: customerData.name,
      policyStatus: customerData.policyStatus
    };
  }

  // Add pet info if available
  if (petData) {
    context.pets = petData.map(pet => ({
      name: pet.name,
      species: pet.species,
      breed: pet.breed
    }));
  }

  // Add claim context if viewing a claim
  if (claimData) {
    context.currentClaim = claimData;
  }

  // Add rich page-specific context
  const pageContext = PAGE_CONTEXT[currentPage] || PAGE_CONTEXT.dashboard;
  context.pageContext = {
    page: currentPage,
    ...pageContext
  };

  return context;
}

export default buildChatContext;
