#
# SPDX-License-Identifier: MIT
#

import os
import glob
from oeqa.utils.commands import bitbake, get_bb_vars
from oeqa.selftest.case import OESelftestTestCase

class Archiver(OESelftestTestCase):

    def test_archiver_allows_to_filter_on_recipe_name(self):
        """
        Summary:     The archiver should offer the possibility to filter on the recipe. (#6929)
        Expected:    1. Included recipe (busybox) should be included
                     2. Excluded recipe (zlib) should be excluded
        Product:     oe-core
        Author:      Daniel Istrate <daniel.alexandrux.istrate@intel.com>
        AutomatedBy: Daniel Istrate <daniel.alexandrux.istrate@intel.com>
        """

        include_recipe = 'busybox'
        exclude_recipe = 'zlib'

        features = 'INHERIT += "archiver"\n'
        features += 'ARCHIVER_MODE[src] = "original"\n'
        features += 'COPYLEFT_PN_INCLUDE = "%s"\n' % include_recipe
        features += 'COPYLEFT_PN_EXCLUDE = "%s"\n' % exclude_recipe
        self.write_config(features)

        bitbake('-c clean %s %s' % (include_recipe, exclude_recipe))
        bitbake("-c deploy_archives %s %s" % (include_recipe, exclude_recipe))

        bb_vars = get_bb_vars(['DEPLOY_DIR_SRC', 'TARGET_SYS'])
        src_path = os.path.join(bb_vars['DEPLOY_DIR_SRC'], bb_vars['TARGET_SYS'])

        # Check that include_recipe was included
        included_present = len(glob.glob(src_path + '/%s-*' % include_recipe))
        self.assertTrue(included_present, 'Recipe %s was not included.' % include_recipe)

        # Check that exclude_recipe was excluded
        excluded_present = len(glob.glob(src_path + '/%s-*' % exclude_recipe))
        self.assertFalse(excluded_present, 'Recipe %s was not excluded.' % exclude_recipe)

    def test_archiver_filters_by_type(self):
        """
        Summary:     The archiver is documented to filter on the recipe type.
        Expected:    1. included recipe type (target) should be included
                     2. other types should be excluded
        Product:     oe-core
        Author:      André Draszik <adraszik@tycoint.com>
        """

        target_recipe = 'initscripts'
        native_recipe = 'zlib-native'

        features = 'INHERIT += "archiver"\n'
        features += 'ARCHIVER_MODE[src] = "original"\n'
        features += 'COPYLEFT_RECIPE_TYPES = "target"\n'
        self.write_config(features)

        bitbake('-c clean %s %s' % (target_recipe, native_recipe))
        bitbake("%s -c deploy_archives %s" % (target_recipe, native_recipe))

        bb_vars = get_bb_vars(['DEPLOY_DIR_SRC', 'TARGET_SYS', 'BUILD_SYS'])
        src_path_target = os.path.join(bb_vars['DEPLOY_DIR_SRC'], bb_vars['TARGET_SYS'])
        src_path_native = os.path.join(bb_vars['DEPLOY_DIR_SRC'], bb_vars['BUILD_SYS'])

        # Check that target_recipe was included
        included_present = len(glob.glob(src_path_target + '/%s-*' % target_recipe))
        self.assertTrue(included_present, 'Recipe %s was not included.' % target_recipe)

        # Check that native_recipe was excluded
        excluded_present = len(glob.glob(src_path_native + '/%s-*' % native_recipe))
        self.assertFalse(excluded_present, 'Recipe %s was not excluded.' % native_recipe)

    def test_archiver_filters_by_type_and_name(self):
        """
        Summary:     Test that the archiver archives by recipe type, taking the
                     recipe name into account.
        Expected:    1. included recipe type (target) should be included
                     2. other types should be excluded
                     3. recipe by name should be included / excluded,
                        overriding previous decision by type
        Product:     oe-core
        Author:      André Draszik <adraszik@tycoint.com>
        """

        target_recipes = [ 'initscripts', 'zlib' ]
        native_recipes = [ 'update-rc.d-native', 'zlib-native' ]

        features = 'INHERIT += "archiver"\n'
        features += 'ARCHIVER_MODE[src] = "original"\n'
        features += 'COPYLEFT_RECIPE_TYPES = "target"\n'
        features += 'COPYLEFT_PN_INCLUDE = "%s"\n' % native_recipes[1]
        features += 'COPYLEFT_PN_EXCLUDE = "%s"\n' % target_recipes[1]
        self.write_config(features)

        bitbake('-c clean %s %s' % (' '.join(target_recipes), ' '.join(native_recipes)))
        bitbake('-c deploy_archives %s %s' % (' '.join(target_recipes), ' '.join(native_recipes)))

        bb_vars = get_bb_vars(['DEPLOY_DIR_SRC', 'TARGET_SYS', 'BUILD_SYS'])
        src_path_target = os.path.join(bb_vars['DEPLOY_DIR_SRC'], bb_vars['TARGET_SYS'])
        src_path_native = os.path.join(bb_vars['DEPLOY_DIR_SRC'], bb_vars['BUILD_SYS'])

        # Check that target_recipe[0] and native_recipes[1] were included
        included_present = len(glob.glob(src_path_target + '/%s-*' % target_recipes[0]))
        self.assertTrue(included_present, 'Recipe %s was not included.' % target_recipes[0])

        included_present = len(glob.glob(src_path_native + '/%s-*' % native_recipes[1]))
        self.assertTrue(included_present, 'Recipe %s was not included.' % native_recipes[1])

        # Check that native_recipes[0] and target_recipes[1] were excluded
        excluded_present = len(glob.glob(src_path_native + '/%s-*' % native_recipes[0]))
        self.assertFalse(excluded_present, 'Recipe %s was not excluded.' % native_recipes[0])

        excluded_present = len(glob.glob(src_path_target + '/%s-*' % target_recipes[1]))
        self.assertFalse(excluded_present, 'Recipe %s was not excluded.' % target_recipes[1])



    def test_archiver_srpm_mode(self):
        """
        Test that in srpm mode, the added recipe dependencies at least exist/work [YOCTO #11121]
        """

        features = 'INHERIT += "archiver"\n'
        features += 'ARCHIVER_MODE[srpm] = "1"\n'
        self.write_config(features)

        bitbake('-n core-image-sato')

    def _test_archiver_mode(self, mode, target_file_name, extra_config=None):
        target = "selftest-ed"

        features = 'INHERIT += "archiver"\n'
        features +=  'ARCHIVER_MODE[src] = "%s"\n' % (mode)
        if extra_config:
            features += extra_config
        self.write_config(features)

        bitbake('-c clean %s' % (target))
        bitbake('-c deploy_archives %s' % (target))

        bb_vars = get_bb_vars(['DEPLOY_DIR_SRC', 'TARGET_SYS'])
        glob_str = os.path.join(bb_vars['DEPLOY_DIR_SRC'], bb_vars['TARGET_SYS'], '%s-*' % (target))
        glob_result = glob.glob(glob_str)
        self.assertTrue(glob_result, 'Missing archiver directory for %s' % (target))

        archive_path = os.path.join(glob_result[0], target_file_name)
        self.assertTrue(os.path.exists(archive_path), 'Missing archive file %s' % (target_file_name))

    def test_archiver_mode_original(self):
        """
        Test that the archiver works in with `ARCHIVER_MODE[src] = "original"`.
        """

        self._test_archiver_mode('original', 'ed-1.14.1.tar.lz')

    def test_archiver_mode_patched(self):
        """
        Test that the archiver works in with `ARCHIVER_MODE[src] = "patched"`.
        """

        self._test_archiver_mode('patched', 'selftest-ed-1.14.1-r0-patched.tar.gz')

    def test_archiver_mode_configured(self):
        """
        Test that the archiver works in with `ARCHIVER_MODE[src] = "configured"`.
        """

        self._test_archiver_mode('configured', 'selftest-ed-1.14.1-r0-configured.tar.gz')

    def test_archiver_mode_recipe(self):
        """
        Test that the archiver works in with `ARCHIVER_MODE[recipe] = "1"`.
        """

        self._test_archiver_mode('patched', 'selftest-ed-1.14.1-r0-recipe.tar.gz',
                                 'ARCHIVER_MODE[recipe] = "1"\n')

    def test_archiver_mode_diff(self):
        """
        Test that the archiver works in with `ARCHIVER_MODE[diff] = "1"`.
        Exclusions controlled by `ARCHIVER_MODE[diff-exclude]` are not yet tested.
        """

        self._test_archiver_mode('patched', 'selftest-ed-1.14.1-r0-diff.gz',
                                 'ARCHIVER_MODE[diff] = "1"\n')

    def test_archiver_mode_dumpdata(self):
        """
        Test that the archiver works in with `ARCHIVER_MODE[dumpdata] = "1"`.
        """

        self._test_archiver_mode('patched', 'selftest-ed-1.14.1-r0-showdata.dump',
                                 'ARCHIVER_MODE[dumpdata] = "1"\n')
