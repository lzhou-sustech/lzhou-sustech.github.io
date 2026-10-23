/* Contributions checked against the linked primary papers. */
window.LZ_RESEARCH_GALLERY = [
  {
    "id": "coding",
    "title": "Source Coding",
    "headline": "Compression beyond first-order rates",
    "question": "How much information is needed when descriptions are shared, refined, or constrained in length?",
    "image": "source-coding.webp",
    "area": [
      1,
      3,
      48,
      31
    ],
    "alt": "Correlated glass terrain sources enter an encoder; common and private streams feed two reconstructions, with coarse-to-fine layers in the foreground.",
    "papers": [
      {
        "title": "Discrete Lossy Gray-Wyner Revisited: Second-Order Asymptotics, Large and Moderate Deviations",
        "year": 2017,
        "url": "https://arxiv.org/abs/1512.01090"
      },
      {
        "title": "Second-Order and Moderate Deviation Asymptotics for Successive Refinement",
        "year": 2017,
        "url": "https://arxiv.org/abs/1601.04500"
      },
      {
        "title": "Non-Asymptotic Converse Bounds and Refined Asymptotics for Two Lossy Source Coding Problems",
        "year": 2019,
        "url": "https://arxiv.org/abs/1708.05496"
      },
      {
        "title": "Achievable Refined Asymptotics for Successive Refinement Using Gaussian Codebooks",
        "year": 2023,
        "url": "https://arxiv.org/abs/2208.03926"
      }
    ],
    "contributions": [
      {
        "title": "Shared and private descriptions",
        "caption": "Characterized the second-order region, reliability, and moderate deviations for discrete lossy Gray–Wyner coding under mild source conditions.",
        "focus": [
          58,
          32
        ],
        "paper": 0
      },
      {
        "title": "Coarse-to-fine reconstruction",
        "caption": "Derived second-order and moderate-deviation limits for successive refinement with joint distortion control.",
        "focus": [
          29,
          77
        ],
        "paper": 1
      },
      {
        "title": "Finite-blocklength converses",
        "caption": "Developed non-asymptotic converse bounds and refined asymptotics for the Kaspi and Fu–Yeung problems. Gaussian-codebook work gives achievable refinements for arbitrary memoryless sources.",
        "focus": [
          43,
          31
        ],
        "paper": 2
      }
    ]
  },
  {
    "id": "inference",
    "title": "Statistical Inference",
    "headline": "Inference with unknown distributions",
    "question": "Which samples are anomalous, which sequences match, and when is there enough evidence to decide?",
    "image": "statistical-inference.webp",
    "area": [
      0.5,
      38,
      38,
      27
    ],
    "alt": "An optical lens highlights a coral outlier among observation streams; paired sample sequences are linked and arriving samples pass a sequential stopping gate.",
    "papers": [
      {
        "title": "Second-Order Asymptotically Optimal Statistical Classification",
        "year": 2020,
        "url": "https://arxiv.org/abs/1806.00739"
      },
      {
        "title": "Second-Order Asymptotically Optimal Outlier Hypothesis Testing",
        "year": 2022,
        "url": "https://arxiv.org/abs/2009.03505"
      },
      {
        "title": "Large and Small Deviations for Statistical Sequence Matching",
        "year": 2024,
        "url": "https://arxiv.org/abs/2407.02816"
      },
      {
        "title": "Sequential Outlier Hypothesis Testing under Universality Constraints",
        "year": 2025,
        "url": "https://arxiv.org/abs/2404.14221"
      },
      {
        "title": "Exponentially Consistent Outlier Hypothesis Testing for Continuous Sequences",
        "year": 2025,
        "url": "https://arxiv.org/abs/2405.01161"
      }
    ],
    "contributions": [
      {
        "title": "Classification and outlier detection",
        "caption": "Derived second-order error tradeoffs for classification and outlier testing with unknown generating distributions, including rejection decisions.",
        "focus": [
          25,
          45
        ],
        "paper": 1
      },
      {
        "title": "Who matches whom?",
        "caption": "Established sequence-matching guarantees in large and small deviations, with optimality for known match counts.",
        "focus": [
          62,
          47
        ],
        "paper": 2
      },
      {
        "title": "Decide as evidence arrives",
        "caption": "Developed outlier tests under universal sample-size constraints, with tight exponent bounds for one outlier. Continuous-observation tests give exponential error guarantees under their stated conditions.",
        "focus": [
          88,
          54
        ],
        "paper": 3
      }
    ]
  },
  {
    "id": "search",
    "title": "Noisy Search",
    "headline": "Finding targets through noisy questions",
    "question": "How accurately can a few noisy questions locate a target?",
    "image": "noisy-search.webp",
    "area": [
      54,
      2,
      44,
      36
    ],
    "alt": "Parallel glass query maps and an adaptive branching sequence narrow uncertainty around moving boat and rover targets.",
    "papers": [
      {
        "title": "Resolution Limits for the Noisy Non-Adaptive 20 Questions Problem",
        "year": 2021,
        "url": "https://arxiv.org/abs/2004.07231"
      },
      {
        "title": "Resolution Limits of Non-Adaptive 20 Questions Search for Multiple Targets",
        "year": 2022,
        "url": "https://arxiv.org/abs/2101.06843"
      },
      {
        "title": "Resolution Limits of Non-Adaptive 20 Questions Search for a Moving Target",
        "year": 2023,
        "url": "https://arxiv.org/abs/2206.08884"
      },
      {
        "title": "Resolution Limits of Non-Adaptive 20 Questions Estimation for Tracking Multiple Moving Targets",
        "year": 2026,
        "url": "https://arxiv.org/abs/2507.02274"
      },
      {
        "title": "Achievable Resolution Limits for the Noisy Adaptive 20 Questions Problem",
        "year": 2021,
        "url": "https://arxiv.org/abs/2105.00265"
      }
    ],
    "contributions": [
      {
        "title": "Finite-query resolution limits",
        "caption": "Non-asymptotic bounds and second-order approximations for non-adaptive search with query-dependent noise.",
        "focus": [
          26,
          16
        ],
        "paper": 0
      },
      {
        "title": "Adaptive querying and stopping",
        "caption": "Achievable adaptive search procedures use variable-length feedback ideas and a termination strategy to improve resolution.",
        "focus": [
          77,
          18
        ],
        "paper": 4
      },
      {
        "title": "Multiple and moving targets",
        "caption": "Resolution bounds extend to multiple targets and unknown motion; a single information-density threshold simplifies multi-target tracking.",
        "focus": [
          65,
          56
        ],
        "paper": 3
      }
    ]
  },
  {
    "id": "security",
    "title": "Security & Privacy",
    "headline": "Security under observation",
    "question": "How can information be useful, secret, and hard to detect?",
    "image": "security-privacy.webp",
    "area": [
      31,
      67,
      39,
      29
    ],
    "alt": "Two transmitters communicate within ambient noise to a receiver holding two separate secret keys; a warden observes and coarse/fine reconstructions sit under a glass shield.",
    "papers": [
      {
        "title": "Capacity Region for Covert Secret Key Generation Over Multiple Access Channels",
        "year": 2026,
        "url": "https://arxiv.org/abs/2504.05828"
      },
      {
        "title": "Successive Refinement of Shannon Cipher System Under Maximal Leakage",
        "year": 2025,
        "url": "https://arxiv.org/abs/2308.07203"
      },
      {
        "title": "Privacy-Utility Tradeoff for Hypothesis Testing Over A Noisy Channel",
        "year": 2021,
        "url": "https://arxiv.org/abs/2006.02869"
      },
      {
        "title": "Collaborative Secret and Covert Communications for Multi-User Multi-Antenna Uplink UAV Systems: Design and Optimization",
        "year": 2025,
        "url": "https://arxiv.org/abs/2407.05738"
      }
    ],
    "contributions": [
      {
        "title": "Covert key generation",
        "caption": "Bounds on the key-rate region for two users sharing separate secret keys with one receiver while hiding the key-generation process.",
        "focus": [
          73,
          35
        ],
        "paper": 0
      },
      {
        "title": "Leakage-aware compression",
        "caption": "The asymptotically optimal normalized maximal-leakage region is characterized for successive refinement under partial-secrecy conditions.",
        "focus": [
          61,
          70
        ],
        "paper": 1
      },
      {
        "title": "Privacy–utility limits",
        "caption": "An exact asymptotic tradeoff and strong converse connect private information leakage to hypothesis-testing performance over a noisy channel.",
        "focus": [
          39,
          35
        ],
        "paper": 2
      }
    ]
  },
  {
    "id": "wireless",
    "title": "Wireless Networks",
    "headline": "From short packets to integrated networks",
    "question": "How should short-packet and integrated networks be designed?",
    "image": "wireless-networks.webp",
    "area": [
      71,
      40,
      28,
      53
    ],
    "alt": "Short packet links connect a multiuser base, UAVs and satellite; a pilot beam diagnoses a coral defective reflecting-surface element beside sea and underwater nodes.",
    "papers": [
      {
        "title": "Achievable Second-Order Asymptotics for MAC and RAC with Additive Non-Gaussian Noise",
        "year": 2025,
        "url": "https://arxiv.org/abs/2410.10312"
      },
      {
        "title": "The Dispersion of Broadcast Channels With Degraded Message Sets Using Spherical Codebooks",
        "year": 2026,
        "url": "https://arxiv.org/abs/2410.17540"
      },
      {
        "title": "Over-the-Air Diagnosis of Defective Elements in Intelligent Reflecting Surface",
        "year": 2026,
        "url": "https://arxiv.org/abs/2408.00379"
      },
      {
        "title": "Efficient User Scheduling for Uplink Hybrid Satellite-Terrestrial Communication",
        "year": 2023,
        "url": "https://arxiv.org/abs/2210.12920"
      },
      {
        "title": "Collaborative Secret and Covert Communications for Multi-User Multi-Antenna Uplink UAV Systems: Design and Optimization",
        "year": 2025,
        "url": "https://arxiv.org/abs/2407.05738"
      }
    ],
    "contributions": [
      {
        "title": "Multiuser finite-blocklength theory",
        "caption": "Second-order achievable rate regions quantify how decoding and non-Gaussian noise affect multiple-access, random-access, and broadcast channels.",
        "focus": [
          41,
          27
        ],
        "paper": 0
      },
      {
        "title": "Over-the-air fault diagnosis",
        "caption": "Noisy twenty-questions methods identify defective intelligent-reflecting-surface elements from reflected pilot measurements.",
        "focus": [
          18,
          49
        ],
        "paper": 2
      },
      {
        "title": "Integrated-network design",
        "caption": "Low-complexity satellite–terrestrial scheduling and collaborative UAV communication designs connect performance analysis to resource allocation.",
        "focus": [
          81,
          15
        ],
        "paper": 3
      }
    ]
  }
];
