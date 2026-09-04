# Post-freeze RF-baseline evidence note

Status: **DOCUMENTED; NOT ADDED TO THE FROZEN V2 MODEL FAMILY**

After the model-family freeze and while V2 target metrics remained blinded, the audit located the authors' public implementation for Cai *et al.*, “Receiver-Agnostic Radio Frequency Fingerprinting via Domain-Invariant Feature Learning,” *IEEE Communications Letters*, vol. 29, no. 10, pp. 2396–2400, 2025, DOI `10.1109/LCOMM.2025.3598034`: [author repository](https://github.com/Edith-xx/Receiver-agnostic-RFFI-CL-).

This evidence corrects the broad earlier statement that no relevant official implementation exists. It does **not** authorize a post-freeze baseline addition. The implementation uses an equalized six-transmitter/twelve-receiver WiSig configuration, a complex-valued student, a Fourier-phase teacher, knowledge distillation, and cross-receiver alignment. Porting it to the fixed 32-receiver raw-I/Q LOSO protocol would introduce architecture, preprocessing, teacher-training, and hyperparameter choices not frozen for V2. The existing V2 suite therefore retains DANN as its generic source-only receiver-adversarial baseline and the official equalized-signal P0/P2/P2-SHUFFLED comparison as a preprocessing diagnostic.

**UNRESOLVED.** A future, separately preregistered source-DG benchmark could reproduce the published equalized twelve-receiver protocol before attempting a 32-receiver extension. It must not be retrofitted after V2 results are available.
