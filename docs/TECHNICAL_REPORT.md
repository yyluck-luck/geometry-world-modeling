# Geometry-aware View Memory: Component Diagnostics and Real RGB-D Controls

Course technical report · September 2026

## Abstract

Geometry-aware view memory uses spatial information to select historical images for camera-controlled scene generation. A change in stored geometry need not change the selected images, and a change in selected images need not improve generation. This report investigates that distinction through component diagnostics derived from a fixed VMem implementation. Synthetic tests isolate first-write position retention and then measure final reference-frame sensitivity at two rendering resolutions. Real-data tests use Kinect depth and motion-capture poses from one TUM RGB-D sequence to compare first-write retention with a simple mean over contributing observation frames. Held-out measurements evaluate depth consistency and selected-image support under shared masks. The real experiment completes eighteen cases and seventy-two paired query conditions, which reuse twelve camera queries from one environment. In the principal unmodified-measurement test, averaging changes none of the eight final reference sets at either resolution. The mean of per-query median depth differences decreases from 30.289 to 27.992 mm, but the mean of per-query mean absolute differences remains 259.265 mm and common prediction support averages only 3.908% of valid target pixels. The coarser sampling condition changes some reference sets with a mean support difference of only 0.021 percentage points. These results support a limited conclusion: position updating affects component statistics, but the principal test does not demonstrate a retrieval benefit. The study provides reproducible controls and negative evidence; it does not establish a novel fusion method, learned-estimator accuracy, or generated-video quality.

## 1. Introduction

Camera-controlled video scene generation requires information about previously observed regions to remain available when the camera changes direction or revisits an earlier view. VMem addresses this problem by associating historical images with the surface elements, or surfels, that they observed, then retrieving relevant images for a target camera [1]. The geometry serves as an index into image memory. This creates a practical distinction between reconstructing the environment accurately and preserving enough geometry to retrieve useful context. For a camera moving around an office desk, the practical question is whether updating stored points changes which earlier photographs the system uses to represent that desk. The present project tests whether a position update reaches the final reference-frame selection and its measured support.

Existing work provides several mechanisms that must be acknowledged before attributing novelty to a new memory rule. CUT3R maintains a persistent state for continuous geometric prediction [2], and Spann3R uses external spatial memory to predict globally aligned pointmaps [3]. ElasticFusion updates surfel maps through repeated observations [4], while probabilistic surfel fusion explicitly models measurement uncertainty during association and fusion [5]. More directly related to generation, I3DM retrieves historical views using implicit three-dimensional features and conditions generation on reliable aligned regions [6]. These precedents make memory, fusion, confidence, and source association insufficient novelty claims by themselves. They also leave a narrower engineering question for this project: what observable consequence does a particular position-update intervention have inside an inspected view-memory component?

Our goal is to diagnose that component using reproducible controls on the available local machine. The study combines synthetic inputs with measured RGB-D observations from the TUM benchmark [7]. It does not train a video generator or evaluate generated videos. In the real-data comparison, supplied depth and motion-capture poses replace learned geometry estimation, allowing the memory update and reference selection to be tested without attributing sensor observations to CUT3R. The comparison is between preservation of the first stored position and a simple mean over contributing observation frames. The latter is an experimental control, without a claim of algorithmic novelty. The scientific question concerns the transfer of a geometric intervention to retrieval, rather than whether averaging can change stored coordinates.

Three issues constrain this diagnosis. First, an implementation effect must be separated from the memory rule: the fixed VMem source contains filtering, source-frame association, and a spatial search whose behaviour matters for controlled inputs. Second, changing rendered support or intermediate scores need not change the final reference set, so evaluation must reach the returned frame identifiers. Third, an update can change which pixels receive a prediction or which source identifiers are stored. A metric defined by each variant's own surviving pixels or source assignments can therefore obscure coverage losses or reward the intervention indirectly. The real-data experiment consequently reports coverage explicitly and evaluates selected images using measurement-derived support masks that are shared by both variants.

The study proceeds through complementary tests. Source inspection and synthetic merge controls isolate the stored-position behaviour and the spatial-index boundary issue (Sections 3.1 and 4.1). Synthetic retrieval tests then compare the complete reference selector under fixed source associations at two resolutions (Sections 3.2 and 4.2). A real RGB-D adapter checks timing and coordinates before the memory comparison uses held-out observations to measure depth consistency and reference support (Sections 3.3–3.6 and 4.3–4.4). This design preserves a distinction between observations that test an interface, interventions that test a mechanism, and evidence that would be needed to assess a full generation system.

The report contributes three course-project artifacts. It documents the behaviour of a fixed baseline component, including negative findings that limit the original failure hypothesis (Sections 4.1–4.2). It provides a traceable measured-data interface and a controlled comparison of two position rules with shared evaluation support (Sections 3.3–3.6). It presents the resulting local evidence with its coverage, sampling, and dependency limits, together with reproducible source and data records (Sections 4–6). These artifacts support further work on geometry-aware view memory; they do not establish a new state-of-the-art method or completion of the original end-to-end video project.

## 2. Related work

### 2.1 Geometry used to retrieve generation context

VMem stores past views and links their identifiers to a coarse surfel representation. It renders those identifiers from the target camera query to retrieve context for novel-view generation [1]. Its paper describes matching new surfels to existing ones and adding the new view index to a matching surfel. The [fixed implementation inspected here](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/modeling/pipeline.py) also contains point-cloud cleaning and confidence/depth filtering. The presence of these mechanisms prevents an accurate description of the baseline as accepting every observation without screening. I3DM instead uses features of a pretrained feed-forward novel-view-synthesis model to score historical views and aligns retrieved information for conditional generation, including reliability selection over aligned regions [6]. Both methods connect spatial information to image context, but their memory representations differ. This report studies the explicit surfel-index route and makes no comparative performance claim against I3DM.

### 2.2 Persistent geometry and external spatial memory

CUT3R updates a recurrent state as new images arrive and predicts pointmaps in a common coordinate system together with camera information [2]. Its authors distinguish online inference, which sees only the available past context, from revisiting after the state has processed the full image sequence. Those settings must not be treated as identical online comparisons. Spann3R maintains an external spatial memory and predicts pointmaps in the first frame's coordinate system without optimization-based global alignment [3]. These methods concern geometric estimation, whereas the external memory in the present experiment indexes reference images. Successful standalone inference with a geometric model would supply a further evidence layer, but would not by itself reproduce VMem's preprocessing, cleaning, alignment, or generation pipeline.

### 2.3 Updating measured surface maps

ElasticFusion combines frame-to-model tracking, windowed surfel fusion, and non-rigid surface correction in an incremental RGB-D mapping system [4]. Park et al. account for measurement uncertainty and surface resolution in LiDAR surfel association and use Bayesian filtering for fusion [5]. These are direct precedents for updating surface estimates and accounting for uncertainty. The frame mean in this report is deliberately a simpler control and is not an implementation of either complete system. Its purpose is to test whether allowing position updates produces a relevant downstream difference under a fixed local protocol. Sensor noise, learned geometry errors, and inconsistent generated content remain distinct error sources.

## 3. Methods

The diagnostic pipeline separates memory construction, geometric evaluation, and reference selection. Synthetic tests inspect specific component behaviours; the real-data path converts depth observations to surfels, constructs one memory per position rule, invokes the fixed reference selector, and scores the results against held-out measurements. The [frozen real-data protocol](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/S2_S3_PROTOCOL.md>) records the data split, parameters, comparisons, and interpretation rules. The implementation uses CPU execution and bypasses learned geometry and image generation throughout S0–S3.

### 3.1 Fixed baseline and synthetic merge controls

The baseline source is VMem revision `39291e4f272f6b4f270691d930926ab5930f942e`. Relevant functions were extracted without changing their abstract syntax trees, and source hashes were recorded in the [provenance manifest](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/vendor/provenance.json>). The inspected [merge function](https://github.com/runjiali-rl/vmem/blob/39291e4f272f6b4f270691d930926ab5930f942e/modeling/pipeline.py) adds a source-frame identifier after a compatible match and retains the stored position. Compatibility combines a distance threshold with a normal dot-product threshold. Matching selects the first compatible candidate encountered in the search order, rather than necessarily the nearest candidate.

S0 applies controlled position perturbations to two synthetic surfel grids and varies perturbation type and strength, seed, observation order, and the number of subsequent correct observations. It contains 216 configurations. S0b repeats 216 configurations using the original function's single-leaf search setting to separate the position rule from a discovered octree boundary issue. Twelve additional index diagnostics compare neighbourhood queries with explicit distance checks. These are component configurations, not independent real scenes. Perturbations enter at the candidate-surfel boundary after the upstream model and its filters have been bypassed. The tests consequently cannot estimate the frequency with which the full baseline admits such errors. The [S0 protocol](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/S0_PROTOCOL.md>) and [S0b amendment](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/S0b_AMENDMENT.md>) preserve the distinction between the initial design and the additional control.

### 3.2 Synthetic retrieval sensitivity

S1 executes the complete fixed VMem reference-selection path through its final returned frame identifiers. Dummy latent and embedding arrays support output packaging only; they do not generate images or determine selection. The synthetic wall has separated coplanar patches. In the shared-history layout, eight historical views share the wall's source coverage. In the partitioned-history layout, twenty views observe different patches, activating the candidate truncation before the final selection of four references. Associations are determined from clean visibility and frozen before perturbation.

The experiment changes positions while holding camera poses, source identifiers, surfel normals and radii, ordering, and selector state fixed. It tests translations of 0, 2, 10, and 40 cm and world-origin depth-scale perturbations of 0, 0.5, 2.5, and 10 percent. Three seeds, two target positions, two resolutions, two layouts, and the perturbation settings produce 192 paired configurations. Clean controls recur across configurations. The non-maximum-suppression threshold is initialized from the same clean first five historical poses and then shared within each pair. Primary outcomes are the final ordered identifiers and frame sets. Intermediate candidate and weight changes are diagnostic outputs, not substitutes for final selection. An auxiliary clean-rendered support measure is retained with its shared-renderer limitation. Full details are in the [S1 protocol](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/S1_PROTOCOL.md>).

### 3.3 Real measurements, association, and temporal split

The real-data path uses TUM RGB-D `freiburg1_xyz` [7]. The archive and extraction records retain the source URL, size, locally computed SHA-256, and timestamps. Integer depth is divided by 5,000 to obtain metres; zero is invalid. The registered-image adapter follows the [official format and calibration guidance](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats), using ROS-default intrinsics with focal lengths 525 pixels and principal point coordinates 319.5 and 239.5 pixels. It applies neither another undistortion nor the Freiburg1 scale factor a second time.

Colour and depth are associated by unique greedy matching with an absolute timestamp difference strictly below 20 ms. Translation is interpolated linearly and orientation by quaternion interpolation at the depth timestamp. Extrapolation and interpolation across a pose gap exceeding 0.1 s are rejected. Colour is not temporally warped to compensate for the residual RGB–depth offset. S2 samples 24 valid observations to inspect timing, missing depth, and projection round trips. A numerically accurate round trip tests the coordinate implementation; it does not validate the physical camera calibration.

S3 divides the valid observation-time interval into three nonoverlapping intervals of equal duration. Each interval contributes 24 samples distributed over its ordered observations: 20 history frames followed by four held-out queries. Block 0 is used for development and implementation checks. Blocks 1 and 2 are evaluation subsets under fixed parameters. These are temporal subsets of a single environment, so they do not constitute three independent scenes or establish cross-scene generalization. Held-out depth is excluded from construction, normal estimation, parameter selection, position updates, and reference selection.

### 3.4 Surfel construction and position rules

Candidates are sampled on a regular pixel grid with stride 16; stride 24 is the prespecified sampling sensitivity check. Normals use the sampled pixel and its immediate right and lower neighbours in the original depth image. Missing measurements and neighbour depth jumps exceeding 0.05 m are rejected identically for both variants. Radii follow the VMem formula with the focal length at the sampling resolution and the viewing-angle factor. The radii represent sparse sampling footprints rather than calibrated uncertainty. Candidate positions and normals are transformed into world coordinates through the supplied optical-camera pose.

An exact cKDTree range query, sorted by stored-point index, reproduces the original single-leaf ordering for matching. The first distance-compatible candidate with a normal dot product strictly above 0.6 is selected. The distance threshold is recomputed per frame as the mean radius plus half its standard deviation over existing and incoming surfels. Small-input comparisons check agreement with the unchanged official merge function. This adapter excludes the default octree's partitioning behaviour; it is not a claim that the default spatial index has been reproduced at scale.

The first-write variant retains a matched surfel's position and adds the source identifier. The frame-mean variant first averages all candidates matched to a stored surfel within the current frame. At the frame boundary it averages that centroid with previous contributing-frame means, counting each frame once. Normals, radii, and colours retain their initial values in both variants. Unmatched candidates are appended after the frame has been processed. Each variant uses its own current positions in later matching, so correspondences, source associations, and map sizes may subsequently differ. This is an online comparison of two update rules, not a comparison under fixed correspondences.

Both variants receive identical observations in identical order. The principal condition uses unmodified measurements. Two additional conditions shift only the first frame's positions by 20 or 50 mm along that source camera's depth axis, after normals and radii have been computed. These errors are injected into measured data and must not be described as naturally occurring CUT3R errors. The full design combines three temporal blocks, two strides, and three perturbation conditions. It specifies eighteen cases, with four held-out queries per case and two retrieval resolutions per query.

### 3.5 Geometric consistency and coverage

Geometric evaluation projects memory centres onto a 160 × 120 grid aligned to original pixels at four-pixel intervals. Rounded projected positions and a nearest-depth buffer determine the predicted depth. The main comparison uses the intersection of pixels predicted by both variants and valid in the held-out measurement. Target validity requires positive finite depth and valid immediate neighbours without a depth jump exceeding 0.05 m. Prediction residuals are not removed for being large. Per-query statistics include mean, median, and 90th-percentile absolute depth difference, signed mean difference, and the fraction within 30 mm. Prediction coverage and the common-support pixel count accompany these values.

Recovery checkpoints follow writes 1, 5, 10, and 20. Besides statistics on each checkpoint's own support, the analysis uses pixels predicted by both variants at every checkpoint. Empty intersections are missing observations, not zero error. Because geometric measurements do not depend on retrieval resolution, they are counted once per query and condition; the two retrieval resolutions do not double the geometric sample count. All depth comparisons assess consistency with sensor measurements. Kinect depth, motion-capture poses, and calibration each have error, and the TUM paper explicitly cautions against treating the supplied poses as a basis for high-accuracy surface reconstruction or evaluation [7].

### 3.6 Reference selection and fixed support

Reference selection retains four frames with translation weight 0.1 and non-maximum suppression. The initial suppression threshold follows the official rule for the first five history poses and is shared by both variants. Optical poses undergo the axis conversion expected by VMem. Retrieval is evaluated at 160 × 120 and 320 × 240 with the original focal-length multiplier of 0.65, preserving its wider field of view. The use of a centred principal point in retrieval differs by less than half a pixel from the scaled TUM principal point and remains an interface approximation.

The reference-support metric is computed independently of either memory's stored source associations. Held-out measured target points are projected into each historical camera. A historical image supports a target pixel when its valid measured depth agrees within 0.05 m, away from missing data and depth boundaries. The union of the selected four historical masks is evaluated on the same target support for both variants. Thus, appending source identifiers cannot by itself increase the score. Auxiliary comparisons select the latest four frames and the four nearest poses; neither uses held-out depth for selection. The nearest-pose control omits suppression and is a practical reference, not a single-factor ablation. The union of all twenty historical masks supplies an upper bound on this particular support measure. None of these metrics measures generated-image fidelity or temporal video quality.

## 4. Results

The results separate source-level and synthetic component tests from sensor-data observations. S0 and S1 do not use real images. S2 checks real-data interfaces. S3 compares update rules using supplied depth and pose observations, with unmodified measurements treated as the principal condition. Descriptive counts do not denote independent scene samples.

### 4.1 First-write behaviour and the spatial-index control

The single-leaf S0b controls retain the first stored position when later observations match it. Table 1 summarizes configurations containing one perturbed and thirteen correct observations, differing in which observation arrives first. Values average two synthetic layouts and three seeds. The positional quantity is distance to discrete reference anchors; a tangential shift of planar anchors is not equivalent to a change in the continuous surface shape. Larger perturbations outside the merge range can retain two point sets instead of replacing the original set. The complete data are preserved in [S0b records](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/results/S0b_leaf_control/>) and summarized in the [S0 report](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/S0_RESULTS.md>).

Table 1. Synthetic first-write order control. Anchor deviation is a descriptive mean in millimetres.

| Perturbation | First observation | Mean anchor deviation (mm) | Surfels |
|---|---|---:|---:|
| Depth scale +0.5%, including seeded variation | Perturbed | 21.05 | 30 |
| Depth scale +0.5%, including seeded variation | Correct | 0.00 | 30 |
| Approximate 2 cm translation | Perturbed | 19.88 | 30 |
| Approximate 2 cm translation | Correct | 0.00 | 30 |

The default index missed existing neighbours on some artificial boundary inputs. In one planar configuration, the memory grew from 30 to 420 surfels; the single-leaf control retained 60. Explicit neighbourhood checks separated this index effect from the first-write rule. The latter remained after controlling the index. Eleven tests passed for the S0 implementation and checks, but neither the controlled point inputs nor the index cases quantify a natural error rate in the full model.

### 4.2 Synthetic retrieval sensitivity

All 192 S1 configurations completed without an exception. Twenty implementation tests passed, and every result contained four valid, distinct reference identifiers. Following an independent diagnostic review, distance-tie checking and returned intrinsics were corrected and the configurations were rerun. Final selections agreed with the initial run for every pair; this rerun is verification, not an additional independent experiment. The [verified S1 records](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/results/S1_retrieval_verified/>) contain intermediate candidates, final identifiers, and paired-resolution checks.

Table 2. Final frame-set changes for the twenty-source synthetic layout. Each denominator is three seeds × two query positions within one artificial layout.

| Perturbation | Lower-resolution changes | Higher-resolution changes | Same combination changed at both resolutions |
|---|---:|---:|---:|
| Translation 2 cm | 1/6 | 0/6 | 0/6 |
| Translation 10 cm | 0/6 | 0/6 | 0/6 |
| Translation 40 cm | 4/6 | 4/6 | 4/6 |
| Depth scale +0.5% | 0/6 | 0/6 | 0/6 |
| Depth scale +2.5% | 2/6 | 0/6 | 0/6 |
| Depth scale +10% | 2/6 | 1/6 | 1/6 |

None of the 72 perturbed configurations in the eight-source shared-history layout changed the final frame set. In the partitioned layout, the small tested errors did not produce changes that persisted across resolutions. The 40 cm translation changed four combinations at both resolutions and reduced their auxiliary clean-reference coverage. Some depth perturbations increased that coverage. The response was therefore neither uniformly harmful nor monotonic in perturbation magnitude. These findings restrict the evidence for small-error retrieval damage under the tested layouts. S0 and S1 are separate interventions: they do not trace a single error through insertion, repeated observation, retained error, and altered retrieval.

### 4.3 Real-data interface checks

The downloaded TUM archive contains 798 RGB images and 798 depth images. Unique timing association yields 792 pairs, of which 789 have admissible pose support; three are rejected. The valid observations span approximately 26.59 s. The archive has 448,204,271 bytes and locally computed SHA-256 `a0236d97b8c30cd93b653656d2b6c293ff7c982a4130ef2a1a8beecdb124ef98`. This hash records the local artifact's identity; it is not described as a comparison with a publisher-provided checksum. The [download manifest](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/data/tum/download_manifest.json>) and [selection manifest](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/results/S2_rgbd_qa/selection_manifest.json>) retain the source and selected observations.

Table 3. S2 interface checks over 24 sampled observations. Round-trip residuals measure numerical implementation consistency, not sensor accuracy.

| Quantity | Observed value |
|---|---:|
| RGB–depth timestamp offset | −8.02 to +16.30 ms |
| Bracketing pose interval | 9.90 to 10.10 ms |
| Valid measured-depth fraction | 68.48% to 79.44% |
| Maximum projection round-trip pixel residual | Approximately 2.56 × 10⁻¹³ pixels |
| Maximum round-trip depth residual | Approximately 3.11 × 10⁻¹⁵ m |

The real-image contact sheet and trajectory plot were visually inspected during S2. The checks support use of the data adapter for the frozen comparison, with missing depth and timing offsets explicitly retained. They do not demonstrate noiseless geometry or eliminate calibration error. Per-frame measurements are available in [frame QA](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/results/S2_rgbd_qa/frame_qa.json>).

### 4.4 Real memory comparison

All eighteen S3 cases completed, producing thirty-six memories, seventy-two paired query conditions, and 144 paired retrieval rows across the two resolutions. These conditions reuse twelve camera queries, including four development queries and eight test queries, in one environment. The run recorded no errors, and independent output verification passed 4,544 checks. The checks include archived-source identity, data integrity, output invariants, and recalculation from saved depth outputs; they are not 4,544 independent performance experiments. The analysis retains all cases in the [case summary](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/results/S3_rgbd_memory/analysis/case_summary.csv>), with [query-level geometry](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/results/S3_rgbd_memory/analysis/query_geometry.csv>) and [query-level retrieval](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/results/S3_rgbd_memory/analysis/query_retrieval.csv>).

Table 4 reports unmodified measurements in the two fixed test blocks. Depth columns are unweighted means of per-query statistics on common prediction pixels, not pooled pixel statistics. In the principal stride-16 condition, no final frame set changes at either retrieval resolution, and selected-image support is identical. The median-based depth summary decreases, but the mean absolute difference remains much larger and predicted-depth coverage also decreases. The common prediction support averages 529.4 pixels per query, or 3.908% of valid target pixels. This sparse intersection sharply limits the area represented by the depth comparison.

Table 4. Unmodified-measurement test results over eight camera queries. FW is first write; FM is frame mean. Coverage values are percentages of valid target pixels.

| Quantity | Stride 16, FW | Stride 16, FM | Stride 24, FW | Stride 24, FM |
|---|---:|---:|---:|---:|
| Mean per-query median absolute depth difference (mm) | 30.289 | 27.992 | 30.683 | 27.755 |
| Mean per-query mean absolute depth difference (mm) | 260.856 | 259.265 | 267.705 | 261.088 |
| Mean own predicted-depth coverage (%) | 10.845 | 10.585 | 4.814 | 4.687 |
| Mean common predicted-depth coverage (%) | 3.908 | 3.908 | 1.547 | 1.547 |
| Mean selected-image support, 160-pixel width (%) | 90.837 | 90.837 | 90.810 | 90.831 |
| Mean stored surfel count per test block | 3,515 | 3,475 | 1,502 | 1,476 |

At stride 24, the same three queries change sets at both resolutions, with matching before-and-after sets across widths. The mean support difference is +0.02098 percentage points at each width. The sampling sensitivity therefore does not provide evidence for a substantial or sampling-stable benefit from averaging. The two temporal test blocks also differ in depth behaviour. At stride 16, block 1 changes from 242.264 to 239.082 mm in mean query absolute difference, whereas block 2 changes from 279.447 to 279.449 mm. A pooled statement that all geometry measures improve would conceal this exception. Figure 1 displays all unmodified-measurement query/stride conditions; its median panel should be read together with the mean errors and coverage in Table 4.

![Paired geometry and measured support for all unmodified test query conditions](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/results/S3_rgbd_memory/analysis/raw_test_paired_comparison.png>)

Figure 1. The principal stride-16 condition leaves measured reference support unchanged for all eight test cameras. Unmodified measurements in the two temporal test blocks are shown. Each point represents a camera query and stride; the two strides reuse the same eight cameras. The left panel compares median depth differences on common prediction pixels. The right panel compares measured reference support, averaged across retrieval widths. The dashed line denotes equality. Neither panel measures video quality, and the left panel does not display the large mean residuals.

The first held-out office view in test block 1 provides a concrete trace of the principal condition. At stride 16 and 160-pixel retrieval width, both rules return historical indices [12, 0, 4, 13], even though candidate membership changes. This earliest test query illustrates how an intermediate change can be absorbed before the final context is returned; the aggregate conclusion still uses all eight test queries.

The artificial first-frame shifts yield a mixed response (Table 5). The stride-16, 50 mm condition produces a larger mean support change than the unmodified case, but it is an injected-error result and remains below one percentage point. At stride 24 with a 20 mm shift, mean selected support decreases. At stride 24 with a 50 mm shift, mean query absolute depth difference increases despite a lower mean query median. These exceptions are retained rather than selecting only favourable cases. Figure 2 shows all development and test cases and distinguishes changes at both widths from identical transitions at both widths.

Table 5. Injected-error test conditions, eight queries per row. Depth differences are FM minus FW in unweighted mean query statistics; negative depth differences are smaller residuals. Support differences are percentage points (pp). The rows reuse cameras and are not independent trials.

| Stride | First-frame shift (mm) | Median-statistic difference (mm) | Mean-absolute-statistic difference (mm) | Set changes, 160 / 320 | Support difference, 160 / 320 (pp) |
|---:|---:|---:|---:|---:|---:|
| 16 | 20 | −3.870 | −5.192 | 4/8 / 4/8 | +0.027 / +0.027 |
| 16 | 50 | −7.393 | −3.309 | 6/8 / 4/8 | +0.765 / +0.804 |
| 24 | 20 | −1.177 | −8.094 | 1/8 / 1/8 | −0.031 / −0.031 |
| 24 | 50 | −0.810 | +1.773 | 2/8 / 2/8 | +0.328 / +0.303 |

![Final selected-set changes for every real-data condition](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/results/S3_rgbd_memory/analysis/resolution_set_change_table.png>)

Figure 2. Final-set changes depend on condition, sampling, and resolution across the eighteen cases. Each denominator is the same four held-out cameras in a temporal block. “Both widths” requires a set change at each width; “same transition” additionally requires identical before-and-after sets across widths. Development outcomes are shown separately from the two fixed test blocks.

The auxiliary reference rules provide an additional check on interpretation (Table 6). In the unmodified stride-16 test condition, both memory variants obtain lower measured support than the latest-four and nearest-pose-four rules. These alternatives do not demonstrate better video generation, and nearest-pose selection differs in suppression behaviour. They do show that a higher complexity selector or a more frequently updated map cannot be assumed to supply greater support in this local sequence. The all-history value uses twenty images and is an upper bound for the mask-union metric, not an equal-budget baseline or an optimum over four-image subsets.

Table 6. Mean measured-image support in the unmodified test condition. The VMem component rows use stride 16 and 160-pixel retrieval width; the two widths yield the same selected sets here.

| Reference rule | Number of historical images | Mean support (%) |
|---|---:|---:|
| First-write memory selector | 4 | 90.837 |
| Frame-mean memory selector | 4 | 90.837 |
| Latest four images | 4 | 92.810 |
| Four nearest poses, without suppression | 4 | 93.820 |
| All historical images | 20 | 96.848 |

In the principal condition, mean memory-build time is 0.148 s for first write and 0.183 s for frame mean over twenty writes. These values describe the small CPU memory construction stage under the recorded run, not full inference latency. The complete S3 run, including evaluation, retrieval, and saving outputs, lasts approximately 305.2 s with two case workers. The map count and predicted-depth coverage decrease under averaging in all eighteen recorded cases; reference support can increase, decrease, or remain unchanged (Figure 3). Full per-step update and checkpoint records remain available alongside each case result.

![Map size, depth coverage, and selected-image support changes](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/results/S3_rgbd_memory/analysis/map_size_and_coverage_changes.png>)

Figure 3. All eighteen builds store fewer points and cover fewer target pixels after frame averaging; reference-support changes have mixed signs. Coverage differences are FM minus FW, averaged over each case's four queries. Memory count is one completed build per rule and case. Predicted-depth coverage and measured reference support have different definitions and must not be interchanged.

## 5. Discussion and limitations

The principal test shows a separation between position statistics and reference selection. Averaging changes stored positions and some depth-consistency summaries. The final reference sets remain identical in the unmodified stride-16 test. The synthetic shared-history control provides another example of the same logical boundary: geometric changes alone need not change the available source set or the final selection. This is consistent with VMem's use of geometry as a coarse index [1]. It does not show that accurate geometry is universally unnecessary; it shows that a particular geometric change cannot be assumed to yield a retrieval benefit.

The measurement results also restrict the interpretation of the depth improvements. Common prediction pixels form a small fraction of valid target support. The mean absolute differences are much larger than the median-based summaries, so typical residuals alone do not characterize the error distribution. Changes in map size and coverage further prevent a claim of overall surface improvement from a lower median on the intersection. Keeping a shared support mask controls the comparison at those pixels, but it does not make the small intersection representative of the entire scene.

A separately recorded [post-hoc residual analysis](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/results/S3_rgbd_memory/posthoc_residuals/summary.json>) examines all eight principal test queries and retains all 4,235 common-pixel residuals. The pooled absolute-residual 90th percentile changes from 999.506 to 1,008.906 mm. These pooled pixel statistics weight queries by their pixel counts and must not replace the prespecified unweighted query summaries. They confirm that large residuals remain after averaging, without identifying their cause. A shared discrete projection bin does not guarantee correspondence to the same physical surface. Sparse visibility and rounded pixel assignment are candidate explanations that require a separate geometric correspondence test; the present diagnostic does not establish that either caused the observed tail. The frozen primary metrics and test parameters remain unchanged.

The perturbation tests demonstrate that position updating can reach final selection under some conditions. Their effects depend on sampling, resolution, and temporal block, and measured support does not always improve. Injecting an error into a sensor-derived first frame does not establish how often a learned estimator creates an analogous error or how the complete VMem cleaning path treats it. The results therefore do not justify a complex reliability gate as an already validated remedy. Existing fusion methods [4, 5] and reliable-memory injection [6] provide relevant comparisons for later work, but this experiment supplies neither a full implementation comparison nor evidence of novelty over those methods.

Three limits remain central. The observations come from one short sequence, with temporally dependent queries and repeated conditions; no independent-scene confidence interval or significance claim is warranted. The geometric input is measured depth with supplied poses, and the surfel-centre evaluator is sparse and distinct from the selector's surfel rendering. The study omits learned confidence, the complete upstream cleaning pipeline, and generated-video evaluation. Standalone CUT3R preparation is recorded separately, and no completed real-image CUT3R inference is included in the evidence used by this report. A successful future run would still need geometric validation and alignment with VMem's fork before supporting a full pipeline claim.

The next experiments should preserve these distinctions. First, evaluate learned geometry from fixed real images and record its preprocessing, confidence, scale, and numerical validity. Second, replay the full baseline cleaning and writing interface to measure whether naturally occurring residual errors change references under matched context budgets. Third, if a repeatable support effect remains across independent scenes, test its relationship to generated-video consistency. A new update mechanism should be evaluated against the original rule, the frame mean, threshold changes, and relevant equal-budget controls. The current negative principal result is retained as evidence rather than replaced by a stronger artificial corruption chosen to support a preferred hypothesis.

## 6. Reproducibility and project scope

The principal S3 run began at 22:41:40 and completed at 22:46:45 on September 5, 2026, Asia/Shanghai time. Its [run metadata](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/results/S3_rgbd_memory/run_metadata.json>) records Python 3.12.14, NumPy 2.3.5, SciPy 1.16.2, PyTorch 2.7.0, Pillow 11.3.0, and Matplotlib 3.10.6 on macOS arm64. Geometry uses float64; the official renderer's depth and the reference-distance sorting retain float32 stages. The experiment does not claim bitwise equivalence with a complete GPU model run. Source snapshots retain the run-time files even when later project work changes the working directory.

The [verification record](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/results/S3_rgbd_memory/verification.json>) and [analysis record](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/results/S3_rgbd_memory/analysis/analysis_summary.json>) record their own source hashes and inputs. The project includes separate [QA](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/scripts/run_rgbd_qa.py>), [experiment](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/scripts/run_rgbd_experiment.py>), [verification](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/scripts/validate_rgbd_outputs.py>), and [analysis](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/scripts/analyze_rgbd_experiment.py>) entry points. The [project README](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/README.md>) supplies execution instructions. New runs should use separate output directories and preserve existing records. PNG figures are previews; vector PDF counterparts and numerical CSVs accompany them.

This report documents the completed component work within the broader Geometry-aware World Modeling project. The original proposal also includes mechanism integration, experiments, and a final presentation or demonstration; learned-geometry and full video-generation evidence remain separate outstanding items in the [delivery tracker](</Users/rocket/Desktop/HKUST IT/ip-/geometry-world-modeling/docs/PROJECT_DELIVERY_TRACKER.md>). Automated run timestamps are not evidence of the student's learning hours, actual supervisor meetings, or final submission. The report is an inspectable technical deliverable for human course review, not a certification that those requirements have been fulfilled.

## 7. Conclusion

The tested memory component can preserve an initially stored position, and changing positions can affect retrieval in selected controlled conditions. However, the principal real-measurement test supplies no final-reference or measured-support benefit from frame averaging. Median depth differences decrease on a sparse common support while large mean residuals and reduced coverage remain. These outcomes support using explicit downstream and coverage controls before claiming that a geometry update improves view memory. They also provide a reproducible basis for deciding whether a more complex mechanism is warranted. Evidence from learned geometry, full baseline cleaning, independent scenes, and generated videos is still required to evaluate the broader project objective.

## References

[1] R. Li, P. Torr, A. Vedaldi, et al., “VMem: Consistent Interactive Video Scene Generation with Surfel-Indexed View Memory,” in Proceedings of the IEEE/CVF International Conference on Computer Vision, 2025, pp. 25690–25699. [Author project and proceedings metadata](https://v-mem.github.io/); [paper, arXiv v3](https://arxiv.org/abs/2506.18903v3).

[2] Q. Wang, Y. Zhang, A. Holynski, et al., “Continuous 3D Perception Model with Persistent State,” in Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, 2025. [Author project](https://cut3r.github.io/); [paper](https://arxiv.org/abs/2501.12387).

[3] H. Wang and L. Agapito, “3D Reconstruction with Spatial Memory,” in Proceedings of the International Conference on 3D Vision, 2025, pp. 78–89. [Author project and proceedings metadata](https://hengyiwang.github.io/projects/spanner); [2024 preprint](https://arxiv.org/abs/2408.16061).

[4] T. Whelan, S. Leutenegger, R. F. Salas-Moreno, et al., “ElasticFusion: Dense SLAM Without A Pose Graph,” in Proceedings of Robotics: Science and Systems, 2015, doi: 10.15607/RSS.2015.XI.001. [Official proceedings](https://www.roboticsproceedings.org/rss11/p01.html); [paper](https://roboticsproceedings.org/rss11/p01.pdf).

[5] C. Park, S. Kim, P. Moghadam, et al., “Probabilistic Surfel Fusion for Dense LiDAR Mapping,” in Proceedings of the IEEE International Conference on Computer Vision Workshops, 2017. [Author-submitted paper and workshop record](https://arxiv.org/abs/1709.01265); [first-author publication page](https://copark86.github.io/publication/2017-10-29-surfelfusion).

[6] J. Li, H. Yan, Y. Chen, et al., “I3DM: Implicit 3D-aware Memory Retrieval and Injection for Consistent Video Scene Generation,” arXiv:2603.23413, 2026. [Paper, v2](https://arxiv.org/abs/2603.23413v2); [author project](https://riga2.github.io/i3dm/).

[7] J. Sturm, N. Engelhard, F. Endres, et al., “A Benchmark for the Evaluation of RGB-D SLAM Systems,” in Proceedings of the IEEE/RSJ International Conference on Intelligent Robots and Systems, 2012. [Official bibliography](https://cvg.cit.tum.de/research/vslam?key=sturm12iros); [author-provided paper](https://jsturm.de/publications/data/sturm12iros.pdf).
