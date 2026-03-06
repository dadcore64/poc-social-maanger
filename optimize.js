const fs = require('fs');
let html = fs.readFileSync('app/templates/login.html', 'utf8');

const optimizedFunctions = 
            const validatePasswordStrength = (val, prefix) => {
                const reqLength = updateReq(\\-length\, val.length >= 8);
                const reqUpper = updateReq(\\-upper\, /[A-Z]/.test(val));
                const reqLower = updateReq(\\-lower\, /[a-z]/.test(val));
                const reqNumber = updateReq(\\-number\, /\d/.test(val));
                const reqSpecial = updateReq(\\-special\, /[^a-zA-Z0-9]/.test(val));
                return reqLength && reqUpper && reqLower && reqNumber && reqSpecial;
            };

            const validateConfirmPassword = (passwordVal, confirmVal, confirmInput, confirmIcon, confirmMsg) => {
                if (confirmVal === '') {
                    confirmIcon.classList.add('hidden');
                    confirmMsg.classList.add('hidden');
                    confirmInput.classList.remove('ring-red-500', 'ring-2');
                    return false;
                } else if (confirmVal === passwordVal) {
                    confirmIcon.classList.remove('hidden', 'fa-xmark', 'text-red-500');
                    confirmIcon.classList.add('fa-check', 'text-green-500');
                    confirmInput.classList.remove('ring-red-500', 'ring-2');
                    confirmMsg.classList.add('hidden');
                    return true;
                } else {
                    confirmIcon.classList.remove('hidden', 'fa-check', 'text-green-500');
                    confirmIcon.classList.add('fa-xmark', 'text-red-500');
                    confirmInput.classList.add('ring-red-500', 'ring-2');
                    confirmMsg.classList.remove('hidden');
                    return false;
                }
            };
;

const oldResetHandler = /resetPasswordInput\.addEventListener\('input', \(e\) => \{[\s\S]*?checkResetFormValidity\(\);\s*\}\);\s*const checkResetConfirmPassword = \(\) => \{[\s\S]*?checkResetFormValidity\(\);\s*\};\s*resetConfirmPasswordInput\.addEventListener\('input', checkResetConfirmPassword\);/;

const newResetHandler = esetPasswordInput.addEventListener('input', (e) => {
                isResetPasswordValid = validatePasswordStrength(e.target.value, 'reset-req');
                if (resetConfirmPasswordInput.value) {
                    isResetConfirmValid = validateConfirmPassword(e.target.value, resetConfirmPasswordInput.value, resetConfirmPasswordInput, resetConfirmIcon, resetConfirmMsg);
                }
                checkResetFormValidity();
            });

            resetConfirmPasswordInput.addEventListener('input', (e) => {
                isResetConfirmValid = validateConfirmPassword(resetPasswordInput.value, e.target.value, resetConfirmPasswordInput, resetConfirmIcon, resetConfirmMsg);
                checkResetFormValidity();
            });;

const oldRegHandler = /regPassword\.addEventListener\('input', \(e\) => \{[\s\S]*?checkFormValidity\(\);\s*\}\);\s*const checkConfirmPassword = \(\) => \{[\s\S]*?checkFormValidity\(\);\s*\};\s*regConfirmPassword\.addEventListener\('input', checkConfirmPassword\);/;

const newRegHandler = egPassword.addEventListener('input', (e) => {
                isPasswordValid = validatePasswordStrength(e.target.value, 'req');
                if (regConfirmPassword.value) {
                    isConfirmValid = validateConfirmPassword(e.target.value, regConfirmPassword.value, regConfirmPassword, confirmIcon, confirmMsg);
                }
                checkFormValidity();
            });

            regConfirmPassword.addEventListener('input', (e) => {
                isConfirmValid = validateConfirmPassword(regPassword.value, e.target.value, regConfirmPassword, confirmIcon, confirmMsg);
                checkFormValidity();
            });;

html = html.replace(/(return passed;\s*\};\s*)/, "" + optimizedFunctions);
html = html.replace(oldResetHandler, newResetHandler);
html = html.replace(oldRegHandler, newRegHandler);

fs.writeFileSync('app/templates/login.html', html);
console.log('Successfully optimized JS logic');
