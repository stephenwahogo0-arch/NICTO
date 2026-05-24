use std::ffi::CString;
use std::os::raw::c_char;

extern "C" {
    fn voice_synth_speak(text: *const c_char, voice: i32, rate: f32) -> i32;
    fn voice_synth_save(text: *const c_char, voice: i32, rate: f32,
                        path: *const c_char) -> i32;
    fn audio_effect_equalize(input: *const f32, len: i32, bands: *const f32,
                             num_bands: i32, output: *mut f32) -> i32;
    fn audio_effect_normalize(input: *const f32, len: i32, target_db: f32,
                              output: *mut f32) -> i32;
}

pub struct VoiceSynth;

impl VoiceSynth {
    pub fn speak(text: &str, voice: i32, rate: f32) -> Result<(), String> {
        let ct = CString::new(text).map_err(|e| format!("CString: {}", e))?;
        let ret = unsafe { voice_synth_speak(ct.as_ptr(), voice, rate) };
        if ret == 0 { Ok(()) } else { Err(format!("voice_synth_speak: {}", ret)) }
    }

    pub fn save(text: &str, voice: i32, rate: f32, path: &str) -> Result<(), String> {
        let ct = CString::new(text).map_err(|e| format!("CString: {}", e))?;
        let cp = CString::new(path).map_err(|e| format!("CString: {}", e))?;
        let ret = unsafe { voice_synth_save(ct.as_ptr(), voice, rate, cp.as_ptr()) };
        if ret == 0 { Ok(()) } else { Err(format!("voice_synth_save: {}", ret)) }
    }
}

pub struct AudioEffects;

impl AudioEffects {
    pub fn equalize(input: &[f32], bands: &[f32]) -> Result<Vec<f32>, String> {
        let mut out = vec![0.0f32; input.len()];
        let ret = unsafe {
            audio_effect_equalize(input.as_ptr(), input.len() as i32,
                                  bands.as_ptr(), bands.len() as i32,
                                  out.as_mut_ptr())
        };
        if ret == 0 { Ok(out) } else { Err(format!("equalize: {}", ret)) }
    }

    pub fn normalize(input: &[f32], target_db: f32) -> Result<Vec<f32>, String> {
        let mut out = vec![0.0f32; input.len()];
        let ret = unsafe {
            audio_effect_normalize(input.as_ptr(), input.len() as i32,
                                   target_db, out.as_mut_ptr())
        };
        if ret == 0 { Ok(out) } else { Err(format!("normalize: {}", ret)) }
    }
}
